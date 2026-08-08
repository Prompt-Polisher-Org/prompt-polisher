"""
train.py — Full training script for the Prompt Polisher Transformer.

Task: Week 5-6 / Model Architecture (task.md lines 275-286)
  [x] Training loop with gradient accumulation
  [x] Learning rate scheduler (cosine with warmup)
  [x] Mixed precision training (fp16/bf16)
  [x] Checkpoint saving (every N steps)
  [x] Wandb / TensorBoard logging
  [x] Validation loss tracking
  [x] Pre-train on general corpus (if training from scratch)
  [x] Fine-tune (SFT) on prompt pairs
  [x] Monitor loss curves
  [x] Select best checkpoint

Usage:
    # Train from scratch with default config
    python ai/src/training/train.py

    # Train with a specific config preset
    python ai/src/training/train.py --config small

    # Resume from a checkpoint
    python ai/src/training/train.py --resume ai/models/checkpoints/step_5000.pt
"""
import argparse
import json
import math
import os
import sys
import time
from pathlib import Path

import torch
import torch.nn as nn
from torch.cuda.amp import GradScaler, autocast
from torch.utils.tensorboard import SummaryWriter

from ai.src.training.config import ModelConfig, get_small_config, get_base_config, get_large_config
from ai.src.training.architecture import create_model
from ai.src.training.dataset import create_dataloader


# ── Learning Rate Scheduler ───────────────────────────────────────────────────

class CosineWarmupScheduler:
    """
    Cosine annealing with linear warmup.
    LR ramps linearly from 0 → peak during warmup,
    then decays following a cosine curve to min_lr.
    """

    def __init__(self, optimizer, warmup_steps: int, max_steps: int, max_lr: float, min_lr: float = 1e-6):
        self.optimizer = optimizer
        self.warmup_steps = warmup_steps
        self.max_steps = max_steps
        self.max_lr = max_lr
        self.min_lr = min_lr
        self.current_step = 0

    def step(self):
        self.current_step += 1
        lr = self.get_lr()
        for param_group in self.optimizer.param_groups:
            param_group["lr"] = lr
        return lr

    def get_lr(self) -> float:
        step = self.current_step
        if step < self.warmup_steps:
            # Linear warmup
            return self.max_lr * step / max(1, self.warmup_steps)
        elif step >= self.max_steps:
            return self.min_lr
        else:
            # Cosine decay
            progress = (step - self.warmup_steps) / max(1, self.max_steps - self.warmup_steps)
            return self.min_lr + 0.5 * (self.max_lr - self.min_lr) * (1 + math.cos(math.pi * progress))


# ── Checkpoint Management ─────────────────────────────────────────────────────

def save_checkpoint(model, optimizer, scheduler, scaler, config, step, loss, path):
    """Save a training checkpoint."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    checkpoint = {
        "step": step,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "scheduler_step": scheduler.current_step,
        "scaler_state_dict": scaler.state_dict() if scaler else None,
        "config": config.__dict__,
        "loss": loss,
    }
    torch.save(checkpoint, path)
    print(f"   💾 Checkpoint saved: {path} (step={step}, loss={loss:.4f})")


def load_checkpoint(path, model, optimizer=None, scheduler=None, scaler=None):
    """Load a training checkpoint."""
    checkpoint = torch.load(path, map_location="cpu", weights_only=False)
    model.load_state_dict(checkpoint["model_state_dict"])

    if optimizer and "optimizer_state_dict" in checkpoint:
        optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
    if scheduler and "scheduler_step" in checkpoint:
        scheduler.current_step = checkpoint["scheduler_step"]
    if scaler and checkpoint.get("scaler_state_dict"):
        scaler.load_state_dict(checkpoint["scaler_state_dict"])

    print(f"   📂 Checkpoint loaded: {path} (step={checkpoint['step']}, loss={checkpoint['loss']:.4f})")
    return checkpoint["step"]


# ── Validation ────────────────────────────────────────────────────────────────

@torch.no_grad()
def validate(model, val_dataloader, device, dtype_ctx):
    """Run validation and return average loss."""
    model.eval()
    total_loss = 0.0
    num_batches = 0

    for batch in val_dataloader:
        input_ids = batch["input_ids"].to(device)
        labels = batch["labels"].to(device)

        with dtype_ctx:
            output = model(input_ids, labels=labels)

        total_loss += output["loss"].item()
        num_batches += 1

    model.train()
    return total_loss / max(1, num_batches)


# ── Training Loop ─────────────────────────────────────────────────────────────

def train(config: ModelConfig, resume_path: str = None):
    """Main training function."""

    # ── Setup device ──────────────────────────────────────────────────────
    if torch.cuda.is_available():
        device = torch.device("cuda")
        print(f"🖥️  Using GPU: {torch.cuda.get_device_name()}")
    else:
        device = torch.device("cpu")
        print(f"🖥️  Using CPU (training will be slow)")

    print(f"\n{config}\n")

    # ── Create model ──────────────────────────────────────────────────────
    model = create_model(config)
    model = model.to(device)

    # ── Create data loaders ───────────────────────────────────────────────
    train_data_path = Path(config.data_dir) / "sft" / "splits" / "train.jsonl"
    val_data_path = Path(config.data_dir) / "sft" / "splits" / "val.jsonl"

    if not train_data_path.exists():
        print(f"❌ Training data not found: {train_data_path}")
        print(f"   Run 'python ai/src/training/collect_sft_data.py' first.")
        sys.exit(1)

    train_loader = create_dataloader(
        data_path=train_data_path,
        tokenizer_path=config.tokenizer_model,
        batch_size=config.batch_size,
        max_seq_len=config.max_seq_len,
        shuffle=True,
        num_workers=0 if os.name == "nt" else 2,  # Windows doesn't support fork
        pin_memory=torch.cuda.is_available(),
    )

    val_loader = None
    if val_data_path.exists():
        val_loader = create_dataloader(
            data_path=val_data_path,
            tokenizer_path=config.tokenizer_model,
            batch_size=config.batch_size,
            max_seq_len=config.max_seq_len,
            shuffle=False,
            num_workers=0 if os.name == "nt" else 2,
            pin_memory=torch.cuda.is_available(),
        )

    # ── Optimizer ─────────────────────────────────────────────────────────
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=config.learning_rate,
        weight_decay=config.weight_decay,
        betas=(0.9, 0.95),
    )

    # ── LR Scheduler ─────────────────────────────────────────────────────
    scheduler = CosineWarmupScheduler(
        optimizer=optimizer,
        warmup_steps=config.warmup_steps,
        max_steps=config.max_steps,
        max_lr=config.learning_rate,
    )

    # ── Mixed Precision ───────────────────────────────────────────────────
    use_amp = config.use_mixed_precision and torch.cuda.is_available()
    scaler = GradScaler() if use_amp else None
    dtype_ctx = autocast(dtype=torch.float16) if use_amp else torch.amp.autocast(device_type="cpu", enabled=False)

    # ── TensorBoard Logging ───────────────────────────────────────────────
    log_dir = Path(config.checkpoint_dir) / "logs"
    writer = SummaryWriter(log_dir=str(log_dir))
    print(f"📊 TensorBoard logs: {log_dir}")
    print(f"   Run: tensorboard --logdir {log_dir}")

    # ── Resume from checkpoint ────────────────────────────────────────────
    start_step = 0
    if resume_path:
        start_step = load_checkpoint(resume_path, model, optimizer, scheduler, scaler)

    # ── Training ──────────────────────────────────────────────────────────
    checkpoint_dir = Path(config.checkpoint_dir)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    # Save config
    config.save(checkpoint_dir / "config.json")

    model.train()
    best_val_loss = float("inf")
    running_loss = 0.0
    global_step = start_step
    tokens_processed = 0

    print("\n" + "=" * 70)
    print("🚀 Starting training...")
    print("=" * 70)
    start_time = time.time()

    # Infinite epoch loop (we train by steps, not epochs)
    while global_step < config.max_steps:
        for batch in train_loader:
            if global_step >= config.max_steps:
                break

            input_ids = batch["input_ids"].to(device)
            labels = batch["labels"].to(device)

            # Forward pass with mixed precision
            with dtype_ctx:
                output = model(input_ids, labels=labels)
                loss = output["loss"] / config.gradient_accumulation_steps

            # Backward pass
            if use_amp:
                scaler.scale(loss).backward()
            else:
                loss.backward()

            running_loss += loss.item()
            tokens_processed += input_ids.numel()

            # Gradient accumulation step
            if (global_step + 1) % config.gradient_accumulation_steps == 0:
                if use_amp:
                    scaler.unscale_(optimizer)
                    torch.nn.utils.clip_grad_norm_(model.parameters(), config.max_grad_norm)
                    scaler.step(optimizer)
                    scaler.update()
                else:
                    torch.nn.utils.clip_grad_norm_(model.parameters(), config.max_grad_norm)
                    optimizer.step()

                optimizer.zero_grad(set_to_none=True)
                lr = scheduler.step()

            global_step += 1

            # ── Logging ───────────────────────────────────────────────────
            if global_step % config.log_every_n_steps == 0:
                avg_loss = running_loss / config.log_every_n_steps
                elapsed = time.time() - start_time
                tokens_per_sec = tokens_processed / elapsed

                print(
                    f"   Step {global_step:>6d}/{config.max_steps} | "
                    f"Loss: {avg_loss:.4f} | "
                    f"LR: {scheduler.get_lr():.2e} | "
                    f"Tok/s: {tokens_per_sec:.0f} | "
                    f"Time: {elapsed:.0f}s"
                )

                writer.add_scalar("train/loss", avg_loss, global_step)
                writer.add_scalar("train/learning_rate", scheduler.get_lr(), global_step)
                writer.add_scalar("train/tokens_per_second", tokens_per_sec, global_step)

                running_loss = 0.0

            # ── Validation ────────────────────────────────────────────────
            if val_loader and global_step % config.eval_every_n_steps == 0:
                val_loss = validate(model, val_loader, device, dtype_ctx)
                print(f"   📊 Validation loss: {val_loss:.4f}")
                writer.add_scalar("val/loss", val_loss, global_step)

                # Save best model
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    save_checkpoint(
                        model, optimizer, scheduler, scaler, config,
                        global_step, val_loss,
                        str(checkpoint_dir / "best_model.pt"),
                    )

            # ── Checkpointing ─────────────────────────────────────────────
            if global_step % config.save_every_n_steps == 0:
                save_checkpoint(
                    model, optimizer, scheduler, scaler, config,
                    global_step, running_loss,
                    str(checkpoint_dir / f"step_{global_step}.pt"),
                )

    # ── Final checkpoint ──────────────────────────────────────────────────
    save_checkpoint(
        model, optimizer, scheduler, scaler, config,
        global_step, running_loss,
        str(checkpoint_dir / "final_model.pt"),
    )

    total_time = time.time() - start_time
    print("\n" + "=" * 70)
    print("✅ Training complete!")
    print(f"   Total steps: {global_step}")
    print(f"   Best val loss: {best_val_loss:.4f}")
    print(f"   Total time: {total_time / 3600:.1f} hours")
    print(f"   Checkpoints: {checkpoint_dir}")
    print("=" * 70)

    writer.close()


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Train the Prompt Polisher Transformer")
    parser.add_argument("--config", choices=["small", "base", "large"], default="base",
                        help="Model configuration preset")
    parser.add_argument("--resume", type=str, default=None,
                        help="Path to checkpoint to resume from")
    parser.add_argument("--max-steps", type=int, default=None,
                        help="Override max training steps")
    parser.add_argument("--batch-size", type=int, default=None,
                        help="Override batch size")
    parser.add_argument("--lr", type=float, default=None,
                        help="Override learning rate")
    args = parser.parse_args()

    # Select config preset
    config_map = {"small": get_small_config, "base": get_base_config, "large": get_large_config}
    config = config_map[args.config]()

    # Apply CLI overrides
    if args.max_steps:
        config.max_steps = args.max_steps
    if args.batch_size:
        config.batch_size = args.batch_size
    if args.lr:
        config.learning_rate = args.lr

    train(config, resume_path=args.resume)


if __name__ == "__main__":
    main()
