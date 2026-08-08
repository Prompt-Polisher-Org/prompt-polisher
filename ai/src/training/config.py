"""
config.py — Model configuration for the Prompt Polisher Transformer.

Task: Week 5-6 / Model Architecture (task.md lines 254-259)
  [x] Number of layers (6-12)
  [x] Hidden dimension (512-768)
  [x] Number of attention heads (8-12)
  [x] Context length (1024-2048 tokens)
  [x] Vocabulary size (32,000)

Provides a dataclass-based config that's easy to serialize/deserialize
and modify for experiments.
"""
from dataclasses import dataclass, asdict, field
import json
from pathlib import Path


@dataclass
class ModelConfig:
    """
    Configuration for the Prompt Polisher Transformer model.

    We use conservative defaults that balance quality with the constraint
    of running on consumer laptops (8-16GB VRAM).
    """

    # ── Architecture ──────────────────────────────────────────────────────
    vocab_size: int = 32_000          # Must match tokenizer vocab
    num_layers: int = 8               # Transformer decoder blocks
    hidden_dim: int = 512             # Hidden/embedding dimension (d_model)
    num_heads: int = 8                # Multi-head attention heads
    head_dim: int = 64                # Per-head dimension (hidden_dim / num_heads)
    intermediate_dim: int = 1408      # FFN intermediate size (~2.75x hidden_dim for SwiGLU)
    max_seq_len: int = 1024           # Maximum context window
    dropout: float = 0.1             # Dropout probability (training only)
    norm_eps: float = 1e-6            # RMSNorm epsilon

    # ── Training ──────────────────────────────────────────────────────────
    learning_rate: float = 3e-4       # Peak LR (AdamW)
    weight_decay: float = 0.01        # L2 regularization
    warmup_steps: int = 500           # LR warmup steps
    max_steps: int = 50_000           # Total training steps
    batch_size: int = 8               # Per-device batch size
    gradient_accumulation_steps: int = 4  # Effective batch = batch_size * grad_accum
    max_grad_norm: float = 1.0        # Gradient clipping

    # ── Precision ─────────────────────────────────────────────────────────
    use_mixed_precision: bool = True  # fp16 / bf16 training
    dtype: str = "float16"            # "float16" or "bfloat16"

    # ── Checkpointing ─────────────────────────────────────────────────────
    save_every_n_steps: int = 1000    # Save checkpoint frequency
    eval_every_n_steps: int = 500     # Run validation frequency
    log_every_n_steps: int = 10       # Log metrics frequency

    # ── Paths ─────────────────────────────────────────────────────────────
    tokenizer_model: str = "ai/models/tokenizer/prompt_polisher_bpe.model"
    checkpoint_dir: str = "ai/models/checkpoints"
    data_dir: str = "ai/data"

    def __post_init__(self):
        """Validate and derive computed fields."""
        assert self.hidden_dim % self.num_heads == 0, \
            f"hidden_dim ({self.hidden_dim}) must be divisible by num_heads ({self.num_heads})"
        self.head_dim = self.hidden_dim // self.num_heads

    @property
    def num_parameters(self) -> int:
        """Estimate total parameter count (approximate)."""
        # Embeddings
        embed = self.vocab_size * self.hidden_dim  # token embeddings
        pos_embed = self.max_seq_len * self.hidden_dim  # positional embeddings

        # Per transformer layer
        # Attention: Q, K, V projections + output projection
        attn = 4 * self.hidden_dim * self.hidden_dim
        # SwiGLU FFN: gate + up + down projections
        ffn = 3 * self.hidden_dim * self.intermediate_dim
        # RMSNorm: 2 per layer (attention + ffn)
        norm = 2 * self.hidden_dim
        per_layer = attn + ffn + norm

        # Final norm + output head
        final = self.hidden_dim + self.vocab_size * self.hidden_dim

        total = embed + pos_embed + (self.num_layers * per_layer) + final
        return total

    @property
    def num_parameters_millions(self) -> float:
        """Estimated parameter count in millions."""
        return self.num_parameters / 1_000_000

    def save(self, path: str | Path):
        """Save config to JSON."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(asdict(self), f, indent=2)

    @classmethod
    def load(cls, path: str | Path) -> "ModelConfig":
        """Load config from JSON."""
        with open(path, "r") as f:
            data = json.load(f)
        return cls(**data)

    def __repr__(self) -> str:
        return (
            f"ModelConfig(\n"
            f"  Architecture: {self.num_layers}L / {self.hidden_dim}D / {self.num_heads}H\n"
            f"  FFN: {self.intermediate_dim} (SwiGLU)\n"
            f"  Vocab: {self.vocab_size:,} | Context: {self.max_seq_len}\n"
            f"  Parameters: ~{self.num_parameters_millions:.1f}M\n"
            f"  Training: bs={self.batch_size}×{self.gradient_accumulation_steps}, lr={self.learning_rate}\n"
            f")"
        )


# ── Preset Configurations ─────────────────────────────────────────────────────

def get_small_config() -> ModelConfig:
    """Small model (~25M params) for quick experiments and debugging."""
    return ModelConfig(
        num_layers=6,
        hidden_dim=384,
        num_heads=6,
        intermediate_dim=1024,
        max_seq_len=512,
    )


def get_base_config() -> ModelConfig:
    """Base model (~45M params) — the default production model."""
    return ModelConfig(
        num_layers=8,
        hidden_dim=512,
        num_heads=8,
        intermediate_dim=1408,
        max_seq_len=1024,
    )


def get_large_config() -> ModelConfig:
    """Large model (~110M params) for when more capacity is needed."""
    return ModelConfig(
        num_layers=12,
        hidden_dim=768,
        num_heads=12,
        intermediate_dim=2048,
        max_seq_len=2048,
        batch_size=4,
        gradient_accumulation_steps=8,
    )


if __name__ == "__main__":
    # Print all presets for reference
    for name, fn in [("Small", get_small_config), ("Base", get_base_config), ("Large", get_large_config)]:
        cfg = fn()
        print(f"{'─'*50}")
        print(f"  {name} Model")
        print(cfg)
