"""
engine.py — Inference engine for the Prompt Polisher Transformer.

Task: Week 5-6 / Inference Engine (task.md lines 301-309)
  [x] Load a trained checkpoint and its SentencePiece tokenizer
  [x] Synchronous generation (returns the full optimized prompt)
  [x] Token-by-token streaming generation
  [x] Sampling controls: temperature, top-k, top-p, repetition penalty

This module is the bridge between the raw `PromptPolisherTransformer`
(which speaks token IDs) and the FastAPI inference server (which speaks
strings). It owns prompt templating, decoding and the sampling loop.

Usage:
    from ai.src.inference.engine import InferenceEngine, GenerationConfig

    engine = InferenceEngine.from_checkpoint("ai/models/checkpoints/final_model.pt")
    result = engine.generate("write me a marketing email")
    print(result["generated_text"])

    for token in engine.stream("write me a marketing email"):
        print(token, end="", flush=True)
"""
from __future__ import annotations

import logging
import time
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import torch
import torch.nn.functional as F
from ai.src.training.architecture import PromptPolisherTransformer
from ai.src.training.config import ModelConfig
from ai.src.training.dataset import INFERENCE_TEMPLATE

logger = logging.getLogger(__name__)


# ── Generation Settings ───────────────────────────────────────────────────────

@dataclass
class GenerationConfig:
    """Sampling parameters for a single generation request."""

    max_new_tokens: int = 512
    temperature: float = 0.7
    top_k: int = 50
    top_p: float = 0.9
    repetition_penalty: float = 1.1


# ── Sampling Helpers ──────────────────────────────────────────────────────────

def _apply_repetition_penalty(
    logits: torch.Tensor, generated_ids: torch.Tensor, penalty: float
) -> torch.Tensor:
    """
    Discourage the model from repeating tokens it has already produced.

    Follows the CTRL formulation: positive logits are divided by `penalty`
    and negative logits are multiplied by it, so both move toward -inf.
    """
    if penalty == 1.0 or generated_ids.numel() == 0:
        return logits

    unique_ids = torch.unique(generated_ids)
    selected = logits[0, unique_ids]
    logits[0, unique_ids] = torch.where(selected > 0, selected / penalty, selected * penalty)
    return logits


def _filter_top_k(logits: torch.Tensor, top_k: int) -> torch.Tensor:
    """Mask out everything outside the `top_k` highest-scoring tokens."""
    if top_k <= 0:
        return logits
    k = min(top_k, logits.size(-1))
    threshold = torch.topk(logits, k)[0][..., -1, None]
    return logits.masked_fill(logits < threshold, float("-inf"))


def _filter_top_p(logits: torch.Tensor, top_p: float) -> torch.Tensor:
    """
    Nucleus sampling: keep the smallest set of tokens whose cumulative
    probability exceeds `top_p`, mask out the rest.
    """
    if top_p >= 1.0:
        return logits

    sorted_logits, sorted_indices = torch.sort(logits, descending=True, dim=-1)
    cumulative_probs = torch.cumsum(F.softmax(sorted_logits, dim=-1), dim=-1)

    # Shift right so the token that crosses the threshold is itself kept.
    remove = cumulative_probs > top_p
    remove[..., 1:] = remove[..., :-1].clone()
    remove[..., 0] = False

    # Map the mask back to the original vocabulary order.
    remove_in_vocab_order = remove.scatter(-1, sorted_indices, remove)
    return logits.masked_fill(remove_in_vocab_order, float("-inf"))


# ── Inference Engine ──────────────────────────────────────────────────────────

class InferenceEngine:
    """
    Wraps a trained model + tokenizer and exposes string-in / string-out
    generation. Instances are stateless between calls, so one engine can
    serve many requests (though the sampling loop itself is synchronous —
    the server runs it off the event loop).
    """

    def __init__(
        self,
        model: PromptPolisherTransformer,
        tokenizer,
        config: ModelConfig,
        device: torch.device,
    ):
        self.model = model
        self.tokenizer = tokenizer
        self.config = config
        self.device = device

        self.model.eval()
        self.model.to(device)

        self.bos_id = tokenizer.bos_id()
        self.eos_id = tokenizer.eos_id()
        self.pad_id = tokenizer.pad_id()

    # ── Construction ──────────────────────────────────────────────────────

    @classmethod
    def from_checkpoint(
        cls,
        checkpoint_path: str | Path,
        device: str | None = None,
        tokenizer_path: str | Path | None = None,
    ) -> InferenceEngine:
        """
        Rebuild an engine from a training checkpoint saved by
        `ai.src.training.train.save_checkpoint`.

        Args:
            checkpoint_path: Path to the .pt checkpoint.
            device: "cpu" / "cuda". Defaults to CUDA when available.
            tokenizer_path: Override for the SentencePiece .model file.
                            Defaults to the path recorded in the checkpoint config.
        """
        checkpoint_path = Path(checkpoint_path)
        if not checkpoint_path.exists():
            raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")

        resolved_device = torch.device(
            device or ("cuda" if torch.cuda.is_available() else "cpu")
        )

        checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)

        # Rebuild the model config that was used during training.
        raw_config = checkpoint.get("config")
        if isinstance(raw_config, ModelConfig):
            model_config = raw_config
        elif isinstance(raw_config, dict):
            known = {f: raw_config[f] for f in ModelConfig.__dataclass_fields__ if f in raw_config}
            model_config = ModelConfig(**known)
        else:
            logger.warning("Checkpoint has no config — falling back to the base preset")
            from ai.src.training.config import get_base_config
            model_config = get_base_config()

        model = PromptPolisherTransformer(model_config)
        model.load_state_dict(checkpoint["model_state_dict"])

        tokenizer = cls._load_tokenizer(tokenizer_path or model_config.tokenizer_model)

        logger.info(
            "Loaded checkpoint %s (step=%s) onto %s",
            checkpoint_path, checkpoint.get("step", "?"), resolved_device,
        )
        return cls(model, tokenizer, model_config, resolved_device)

    @staticmethod
    def _load_tokenizer(tokenizer_path: str | Path):
        """Load the trained SentencePiece tokenizer."""
        import sentencepiece as spm

        tokenizer_path = Path(tokenizer_path)
        if not tokenizer_path.exists():
            raise FileNotFoundError(
                f"Tokenizer not found: {tokenizer_path}. "
                "Train one with `python -m ai.src.tokenizer.train_tokenizer`."
            )

        tokenizer = spm.SentencePieceProcessor()
        tokenizer.load(str(tokenizer_path))
        return tokenizer

    # ── Prompt Handling ───────────────────────────────────────────────────

    def _encode_prompt(self, prompt: str) -> torch.Tensor:
        """Wrap a raw user prompt in the training instruction template and tokenize it."""
        text = INFERENCE_TEMPLATE.format(input_prompt=prompt)
        token_ids = self.tokenizer.encode(text, out_type=int)

        # Leave room for the response inside the model's context window.
        max_prompt_len = max(1, self.config.max_seq_len - 1)
        if len(token_ids) > max_prompt_len:
            token_ids = token_ids[-max_prompt_len:]

        return torch.tensor([token_ids], dtype=torch.long, device=self.device)

    # ── Core Sampling Loop ────────────────────────────────────────────────

    @torch.no_grad()
    def _sample_ids(
        self, input_ids: torch.Tensor, gen_config: GenerationConfig
    ) -> Iterator[int]:
        """
        Yield generated token IDs one at a time.

        Both `generate` and `stream` are built on top of this so the two
        paths can never drift apart.
        """
        generated: list[int] = []

        for _ in range(gen_config.max_new_tokens):
            # Crop to the context window.
            context = input_ids[:, -self.config.max_seq_len:]

            logits = self.model(context)["logits"][:, -1, :].float()

            if gen_config.repetition_penalty != 1.0 and generated:
                penalty_ids = torch.tensor(generated, dtype=torch.long, device=self.device)
                logits = _apply_repetition_penalty(
                    logits, penalty_ids, gen_config.repetition_penalty
                )

            if gen_config.temperature > 0:
                logits = logits / gen_config.temperature
                logits = _filter_top_k(logits, gen_config.top_k)
                logits = _filter_top_p(logits, gen_config.top_p)
                probs = F.softmax(logits, dim=-1)
                next_token = torch.multinomial(probs, num_samples=1)
            else:
                # temperature == 0 → greedy decoding
                next_token = logits.argmax(dim=-1, keepdim=True)

            token_id = int(next_token.item())
            if token_id == self.eos_id:
                break

            generated.append(token_id)
            input_ids = torch.cat([input_ids, next_token], dim=1)
            yield token_id

    # ── Public API ────────────────────────────────────────────────────────

    def generate(
        self,
        prompt: str,
        gen_config: GenerationConfig | None = None,
        **overrides,
    ) -> dict:
        """
        Generate an optimized prompt and return it in one piece.

        Returns:
            dict with "generated_text", "token_count" and "latency_ms" —
            the exact shape the inference server's GenerateResponse expects.
        """
        gen_config = self._resolve_config(gen_config, overrides)

        start = time.perf_counter()
        input_ids = self._encode_prompt(prompt)
        token_ids = list(self._sample_ids(input_ids, gen_config))
        latency_ms = (time.perf_counter() - start) * 1000.0

        return {
            "generated_text": self.tokenizer.decode(token_ids).strip(),
            "token_count": len(token_ids),
            "latency_ms": latency_ms,
        }

    def stream(
        self,
        prompt: str,
        gen_config: GenerationConfig | None = None,
        **overrides,
    ) -> Iterator[str]:
        """
        Generate an optimized prompt, yielding text as it is produced.

        SentencePiece pieces are sub-word, so we decode the running prefix
        and yield only the delta. That keeps multi-byte characters and
        word-boundary markers intact instead of emitting mojibake.
        """
        gen_config = self._resolve_config(gen_config, overrides)

        input_ids = self._encode_prompt(prompt)
        token_ids: list[int] = []
        decoded_so_far = ""

        for token_id in self._sample_ids(input_ids, gen_config):
            token_ids.append(token_id)
            decoded = self.tokenizer.decode(token_ids)
            delta, decoded_so_far = decoded[len(decoded_so_far):], decoded
            if delta:
                yield delta

    def get_model_info(self) -> dict:
        """Describe the loaded model — surfaced by the server's /health endpoint."""
        return {
            "parameters": self.model.count_parameters(),
            "parameters_millions": round(self.model.count_parameters() / 1e6, 1),
            "num_layers": self.config.num_layers,
            "hidden_dim": self.config.hidden_dim,
            "num_heads": self.config.num_heads,
            "max_seq_len": self.config.max_seq_len,
            "vocab_size": self.config.vocab_size,
            "device": str(self.device),
        }

    # ── Internals ─────────────────────────────────────────────────────────

    @staticmethod
    def _resolve_config(
        gen_config: GenerationConfig | None, overrides: dict
    ) -> GenerationConfig:
        """Merge an optional GenerationConfig with per-call keyword overrides."""
        config = gen_config or GenerationConfig()
        if not overrides:
            return config

        unknown = set(overrides) - set(GenerationConfig.__dataclass_fields__)
        if unknown:
            raise TypeError(f"Unknown generation parameter(s): {', '.join(sorted(unknown))}")

        return GenerationConfig(**{**config.__dict__, **overrides})
