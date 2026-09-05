"""
dpo_trainer.py — Direct Preference Optimization (DPO) Training Pipeline.

Task: Week 11-12 / RLHF (task.md lines 588-610)
  [x] Load (prompt, chosen, rejected) triples
  [x] DPO loss function implementation
  [x] Training loop with gradient accumulation
  [x] Checkpoint saving

DPO is simpler than PPO — it directly optimizes the model to prefer
"chosen" responses over "rejected" responses without needing a separate
reward model. This is the recommended approach for our compute budget.

Reference: "Direct Preference Optimization: Your Language Model is
Secretly a Reward Model" (Rafailov et al., 2023)

Usage:
    python -m ai.src.training.dpo_trainer \
        --feedback_data ai/data/feedback/dpo_triples.jsonl \
        --base_checkpoint ai/models/checkpoints/sft_best.pt \
        --output_dir ai/models/checkpoints/dpo
"""

import json
import math
import time
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader

from ai.src.training.config import ModelConfig, get_small_config, get_base_config, get_large_config
from ai.src.training.architecture import create_model

logger = logging.getLogger(__name__)


# ── DPO Configuration ─────────────────────────────────────────────────────────

@dataclass
class DPOConfig:
    """Configuration for DPO training."""
    # Data
    feedback_data_path: str = "ai/data/feedback/dpo_triples.jsonl"
    max_seq_len: int = 512

    # DPO hyperparameters
    beta: float = 0.1           # KL penalty coefficient (higher = more conservative)
    learning_rate: float = 5e-6  # Lower LR than SFT to avoid catastrophic forgetting
    weight_decay: float = 0.01
    max_steps: int = 2000
    batch_size: int = 4
    gradient_accumulation_steps: int = 4
    max_grad_norm: float = 1.0
    warmup_steps: int = 100

    # Checkpointing
    save_every_n_steps: int = 200
    eval_every_n_steps: int = 100
    log_every_n_steps: int = 10
    output_dir: str = "ai/models/checkpoints/dpo"

    # Model
    base_checkpoint: str = "ai/models/checkpoints/sft_best.pt"
    model_config: ModelConfig = field(default_factory=get_base_config)

    # Precision
    use_mixed_precision: bool = True


# ── DPO Dataset ────────────────────────────────────────────────────────────────

class DPODataset(Dataset):
    """
    Loads (prompt, chosen, rejected) triples for DPO training.

    Expected JSONL format:
    {"prompt": "...", "chosen": "...", "rejected": "..."}
    """

    def __init__(self, data_path: str, max_seq_len: int = 512):
        self.max_seq_len = max_seq_len
        self.data = []

        data_file = Path(data_path)
        if not data_file.exists():
            logger.warning(f"DPO data file not found: {data_path}")
            return

        with open(data_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    if all(k in entry for k in ("prompt", "chosen", "rejected")):
                        self.data.append(entry)
                except json.JSONDecodeError:
                    continue

        logger.info(f"Loaded {len(self.data)} DPO triples from {data_path}")

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return self.data[idx]


def collate_dpo(batch, tokenizer, max_seq_len: int = 512):
    """
    Tokenize and collate a batch of DPO triples.

    Returns:
        dict with keys:
            prompt_ids: (B, L_prompt)
            chosen_ids: (B, L_chosen)
            rejected_ids: (B, L_rejected)
            chosen_labels: (B, L_chosen)  — -100 for prompt tokens
            rejected_labels: (B, L_rejected) — -100 for prompt tokens
    """
    prompt_texts = [item["prompt"] for item in batch]
    chosen_texts = [item["prompt"] + item["chosen"] for item in batch]
    rejected_texts = [item["prompt"] + item["rejected"] for item in batch]

    def tokenize_and_pad(texts, max_len):
        """Tokenize texts and pad to uniform length."""
        encoded = [tokenizer.encode(t)[:max_len] for t in texts]
        max_actual = max(len(e) for e in encoded)
        padded = []
        masks = []
        for e in encoded:
            pad_len = max_actual - len(e)
            padded.append(e + [tokenizer.pad_id()] * pad_len)
            masks.append([1] * len(e) + [0] * pad_len)
        return torch.tensor(padded, dtype=torch.long), torch.tensor(masks, dtype=torch.long)

    # Tokenize prompts to find their length (for masking labels)
    prompt_encoded = [tokenizer.encode(p) for p in prompt_texts]
    prompt_lengths = [len(p) for p in prompt_encoded]

    chosen_ids, chosen_mask = tokenize_and_pad(chosen_texts, max_seq_len)
    rejected_ids, rejected_mask = tokenize_and_pad(rejected_texts, max_seq_len)

    # Create labels: -100 for prompt tokens (we only compute loss on the response)
    chosen_labels = chosen_ids.clone()
    rejected_labels = rejected_ids.clone()

    for i, p_len in enumerate(prompt_lengths):
        chosen_labels[i, :p_len] = -100
        rejected_labels[i, :p_len] = -100

    # Also mask padding
    chosen_labels[chosen_mask == 0] = -100
    rejected_labels[rejected_mask == 0] = -100

    return {
        "chosen_ids": chosen_ids,
        "rejected_ids": rejected_ids,
        "chosen_labels": chosen_labels,
        "rejected_labels": rejected_labels,
        "chosen_mask": chosen_mask,
        "rejected_mask": rejected_mask,
    }


# ── DPO Loss Function ─────────────────────────────────────────────────────────

def compute_dpo_loss(
    policy_chosen_logps: torch.Tensor,
    policy_rejected_logps: torch.Tensor,
    ref_chosen_logps: torch.Tensor,
    ref_rejected_logps: torch.Tensor,
    beta: float = 0.1,
) -> tuple[torch.Tensor, dict]:
    """
    Compute the DPO loss.

    DPO loss = -log(sigmoid(beta * (log(pi(y_w|x)/pi_ref(y_w|x))
                                   - log(pi(y_l|x)/pi_ref(y_l|x)))))

    Where:
        y_w = chosen (winning) response
        y_l = rejected (losing) response
        pi = policy model (being trained)
        pi_ref = reference model (frozen SFT checkpoint)

    Args:
        policy_chosen_logps: Log probs of chosen responses under policy
        policy_rejected_logps: Log probs of rejected responses under policy
        ref_chosen_logps: Log probs of chosen responses under reference
        ref_rejected_logps: Log probs of rejected responses under reference
        beta: KL penalty coefficient

    Returns:
        loss: scalar DPO loss
        metrics: dict with reward margins and accuracies
    """
    # Log-ratios
    chosen_rewards = beta * (policy_chosen_logps - ref_chosen_logps)
    rejected_rewards = beta * (policy_rejected_logps - ref_rejected_logps)

    # DPO loss: -log(sigmoid(chosen_reward - rejected_reward))
    reward_margin = chosen_rewards - rejected_rewards
    loss = -F.logsigmoid(reward_margin).mean()

    # Metrics for logging
    with torch.no_grad():
        accuracy = (reward_margin > 0).float().mean().item()
        chosen_reward_mean = chosen_rewards.mean().item()
        rejected_reward_mean = rejected_rewards.mean().item()

    metrics = {
        "loss": loss.item(),
        "accuracy": accuracy,
        "chosen_reward": chosen_reward_mean,
        "rejected_reward": rejected_reward_mean,
        "reward_margin": reward_margin.mean().item(),
    }

    return loss, metrics


def get_per_token_logps(model, input_ids, labels):
    """
    Compute per-token log probabilities for a sequence.
    Returns the sum of log probs over non-masked tokens.
    """
    outputs = model(input_ids, labels=None)
    logits = outputs["logits"]

    # Shift: logits[:, :-1] predicts labels[:, 1:]
    shift_logits = logits[:, :-1, :]
    shift_labels = labels[:, 1:]

    # Per-token log probabilities
    log_probs = F.log_softmax(shift_logits, dim=-1)
    
    # Prevent gather out-of-bounds on -100 labels
    gather_indices = shift_labels.clone()
    gather_indices[gather_indices == -100] = 0
    
    per_token_logps = log_probs.gather(2, gather_indices.unsqueeze(2)).squeeze(2)

    # Mask out ignored positions (-100)
    mask = (shift_labels != -100).float()
    per_token_logps = per_token_logps * mask

    # Sum over sequence (average would also work, but sum is standard for DPO)
    return per_token_logps.sum(dim=-1)


# ── DPO Trainer ────────────────────────────────────────────────────────────────

class DPOTrainer:
    """
    Direct Preference Optimization trainer.

    Trains a policy model to prefer chosen responses over rejected ones
    relative to a frozen reference model (the initial SFT checkpoint).
    """

    def __init__(self, config: DPOConfig):
        self.config = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        logger.info(f"DPO Trainer initialized on device: {self.device}")
        logger.info(f"Beta: {config.beta}, LR: {config.learning_rate}")

        # Create output directory
        Path(config.output_dir).mkdir(parents=True, exist_ok=True)

    def train(self):
        """Run the full DPO training loop."""
        cfg = self.config

        # ── 1. Load models ─────────────────────────────────────────────────
        logger.info("Loading policy model (trainable)...")
        policy_model = create_model(cfg.model_config).to(self.device)

        logger.info("Loading reference model (frozen)...")
        ref_model = create_model(cfg.model_config).to(self.device)

        # Load SFT checkpoint into both models
        checkpoint_path = Path(cfg.base_checkpoint)
        if checkpoint_path.exists():
            state_dict = torch.load(checkpoint_path, map_location=self.device, weights_only=True)
            if "model_state_dict" in state_dict:
                state_dict = state_dict["model_state_dict"]
            policy_model.load_state_dict(state_dict)
            ref_model.load_state_dict(state_dict)
            logger.info(f"Loaded SFT checkpoint: {checkpoint_path}")
        else:
            logger.warning(f"No SFT checkpoint found at {checkpoint_path}. "
                          "Training from randomly initialized weights (not recommended).")

        # Freeze reference model
        ref_model.eval()
        for param in ref_model.parameters():
            param.requires_grad = False

        # ── 2. Load tokenizer ──────────────────────────────────────────────
        try:
            import sentencepiece as spm
            sp = spm.SentencePieceProcessor()
            tokenizer_path = cfg.model_config.tokenizer_model
            sp.load(tokenizer_path)
            logger.info(f"Loaded tokenizer: {tokenizer_path}")
        except Exception as e:
            logger.error(f"Failed to load tokenizer: {e}")
            raise

        # ── 3. Load dataset ────────────────────────────────────────────────
        dataset = DPODataset(cfg.feedback_data_path, cfg.max_seq_len)
        if len(dataset) == 0:
            logger.error("No DPO training data found. Aborting.")
            return

        dataloader = DataLoader(
            dataset,
            batch_size=cfg.batch_size,
            shuffle=True,
            collate_fn=lambda batch: collate_dpo(batch, sp, cfg.max_seq_len),
            drop_last=True,
        )

        # ── 4. Optimizer ───────────────────────────────────────────────────
        optimizer = torch.optim.AdamW(
            policy_model.parameters(),
            lr=cfg.learning_rate,
            weight_decay=cfg.weight_decay,
            betas=(0.9, 0.95),
        )

        # Linear warmup then cosine decay
        def lr_schedule(step):
            if step < cfg.warmup_steps:
                return step / max(1, cfg.warmup_steps)
            progress = (step - cfg.warmup_steps) / max(1, cfg.max_steps - cfg.warmup_steps)
            return 0.5 * (1 + math.cos(math.pi * progress))

        scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lr_schedule)

        # Mixed precision
        scaler = torch.amp.GradScaler("cuda") if cfg.use_mixed_precision and self.device.type == "cuda" else None

        # ── 5. Training loop ───────────────────────────────────────────────
        logger.info(f"Starting DPO training: {cfg.max_steps} steps, "
                    f"effective batch = {cfg.batch_size * cfg.gradient_accumulation_steps}")

        global_step = 0
        best_accuracy = 0.0
        running_metrics = {"loss": 0, "accuracy": 0, "reward_margin": 0}

        policy_model.train()
        start_time = time.time()

        while global_step < cfg.max_steps:
            for batch in dataloader:
                if global_step >= cfg.max_steps:
                    break

                # Move batch to device
                chosen_ids = batch["chosen_ids"].to(self.device)
                rejected_ids = batch["rejected_ids"].to(self.device)
                chosen_labels = batch["chosen_labels"].to(self.device)
                rejected_labels = batch["rejected_labels"].to(self.device)

                # Forward pass with mixed precision
                with torch.amp.autocast("cuda", enabled=(scaler is not None)):
                    # Policy log-probs
                    policy_chosen_logps = get_per_token_logps(
                        policy_model, chosen_ids, chosen_labels
                    )
                    policy_rejected_logps = get_per_token_logps(
                        policy_model, rejected_ids, rejected_labels
                    )

                    # Reference log-probs (no gradient)
                    with torch.no_grad():
                        ref_chosen_logps = get_per_token_logps(
                            ref_model, chosen_ids, chosen_labels
                        )
                        ref_rejected_logps = get_per_token_logps(
                            ref_model, rejected_ids, rejected_labels
                        )

                    # Compute DPO loss
                    loss, metrics = compute_dpo_loss(
                        policy_chosen_logps,
                        policy_rejected_logps,
                        ref_chosen_logps,
                        ref_rejected_logps,
                        beta=cfg.beta,
                    )
                    loss = loss / cfg.gradient_accumulation_steps

                # Backward pass
                if scaler:
                    scaler.scale(loss).backward()
                else:
                    loss.backward()

                # Accumulate metrics
                for k in running_metrics:
                    running_metrics[k] += metrics.get(k, 0)

                # Optimizer step every N accumulation steps
                if (global_step + 1) % cfg.gradient_accumulation_steps == 0:
                    if scaler:
                        scaler.unscale_(optimizer)
                    torch.nn.utils.clip_grad_norm_(policy_model.parameters(), cfg.max_grad_norm)

                    if scaler:
                        scaler.step(optimizer)
                        scaler.update()
                    else:
                        optimizer.step()

                    scheduler.step()
                    optimizer.zero_grad()

                global_step += 1

                # ── Logging ────────────────────────────────────────────────
                if global_step % cfg.log_every_n_steps == 0:
                    n = cfg.log_every_n_steps
                    avg_metrics = {k: v / n for k, v in running_metrics.items()}
                    elapsed = time.time() - start_time
                    steps_per_sec = global_step / elapsed

                    logger.info(
                        f"Step {global_step}/{cfg.max_steps} | "
                        f"Loss: {avg_metrics['loss']:.4f} | "
                        f"Acc: {avg_metrics['accuracy']:.2%} | "
                        f"Margin: {avg_metrics['reward_margin']:.3f} | "
                        f"LR: {scheduler.get_last_lr()[0]:.2e} | "
                        f"Speed: {steps_per_sec:.1f} steps/s"
                    )
                    running_metrics = {k: 0 for k in running_metrics}

                # ── Checkpointing ──────────────────────────────────────────
                if global_step % cfg.save_every_n_steps == 0:
                    ckpt_path = Path(cfg.output_dir) / f"dpo_step_{global_step}.pt"
                    torch.save({
                        "model_state_dict": policy_model.state_dict(),
                        "optimizer_state_dict": optimizer.state_dict(),
                        "scheduler_state_dict": scheduler.state_dict(),
                        "global_step": global_step,
                        "config": cfg,
                        "metrics": metrics,
                    }, ckpt_path)
                    logger.info(f"Saved checkpoint: {ckpt_path}")

                    # Track best accuracy
                    if metrics["accuracy"] > best_accuracy:
                        best_accuracy = metrics["accuracy"]
                        best_path = Path(cfg.output_dir) / "dpo_best.pt"
                        torch.save({
                            "model_state_dict": policy_model.state_dict(),
                            "global_step": global_step,
                            "accuracy": best_accuracy,
                        }, best_path)
                        logger.info(f"New best accuracy: {best_accuracy:.2%} → saved to {best_path}")

        # ── Final save ─────────────────────────────────────────────────────
        total_time = time.time() - start_time
        final_path = Path(cfg.output_dir) / "dpo_final.pt"
        torch.save({
            "model_state_dict": policy_model.state_dict(),
            "global_step": global_step,
            "total_time_seconds": total_time,
        }, final_path)

        logger.info(f"{'=' * 60}")
        logger.info(f"DPO Training Complete!")
        logger.info(f"  Total steps: {global_step}")
        logger.info(f"  Total time: {total_time / 60:.1f} minutes")
        logger.info(f"  Best accuracy: {best_accuracy:.2%}")
        logger.info(f"  Final checkpoint: {final_path}")
        logger.info(f"{'=' * 60}")


# ── CLI Entry Point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="DPO Training for Prompt Polisher")
    parser.add_argument("--feedback_data", type=str, default="ai/data/feedback/dpo_triples.jsonl")
    parser.add_argument("--base_checkpoint", type=str, default="ai/models/checkpoints/sft_best.pt")
    parser.add_argument("--output_dir", type=str, default="ai/models/checkpoints/dpo")
    parser.add_argument("--beta", type=float, default=0.1)
    parser.add_argument("--lr", type=float, default=5e-6)
    parser.add_argument("--max_steps", type=int, default=2000)
    parser.add_argument("--batch_size", type=int, default=4)
    parser.add_argument("--config", type=str, default="base", choices=["small", "base", "large"])
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

    if args.config == "small":
        model_config = get_small_config()
    elif args.config == "large":
        model_config = get_large_config()
    else:
        model_config = get_base_config()

    config = DPOConfig(
        feedback_data_path=args.feedback_data,
        base_checkpoint=args.base_checkpoint,
        output_dir=args.output_dir,
        beta=args.beta,
        learning_rate=args.lr,
        max_steps=args.max_steps,
        batch_size=args.batch_size,
        model_config=model_config,
    )

    trainer = DPOTrainer(config)
    trainer.train()
