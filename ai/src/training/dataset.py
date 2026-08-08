"""
dataset.py — PyTorch Dataset for SFT training data.

Task: Week 5-6 / Model Architecture (task.md lines 266-270)
  [x] Load and tokenize training data
  [x] Create train/val/test splits
  [x] Implement collate function with padding
  [x] Data loading with DataLoader (num_workers, pin_memory)

Handles loading instruction-tuned (bad_prompt → optimized_prompt) pairs,
tokenizing them with our trained SentencePiece tokenizer, and preparing
them for causal language model training.
"""
import json
import random
from pathlib import Path
from typing import Optional

import torch
from torch.utils.data import Dataset, DataLoader
import sentencepiece as spm


# ── Instruction Template ──────────────────────────────────────────────────────

# This template wraps each (input_prompt, output_prompt) pair into a format
# that teaches the model to follow instructions.
INSTRUCTION_TEMPLATE = (
    "<bos>### Instruction:\n"
    "Optimize the following prompt to be more effective, specific, and detailed.\n\n"
    "### Input Prompt:\n"
    "{input_prompt}\n\n"
    "### Optimized Prompt:\n"
    "{output_prompt}<eos>"
)

# For inference, we stop at "### Optimized Prompt:\n" and let the model generate
INFERENCE_TEMPLATE = (
    "<bos>### Instruction:\n"
    "Optimize the following prompt to be more effective, specific, and detailed.\n\n"
    "### Input Prompt:\n"
    "{input_prompt}\n\n"
    "### Optimized Prompt:\n"
)


# ── Dataset Class ─────────────────────────────────────────────────────────────

class PromptPairDataset(Dataset):
    """
    PyTorch Dataset for (bad_prompt → optimized_prompt) pairs.

    Expected data format (JSONL):
        {"input": "Write about dogs", "output": "Write a 500-word blog post about..."}
        {"input": "Explain AI", "output": "Explain artificial intelligence to a..."}

    Each example is formatted using the instruction template, tokenized,
    and prepared for causal LM training (labels = input_ids shifted right,
    with instruction portion masked out so loss is only on the output).
    """

    def __init__(
        self,
        data_path: str | Path,
        tokenizer_path: str | Path,
        max_seq_len: int = 1024,
        mask_instruction: bool = True,
    ):
        """
        Args:
            data_path: Path to JSONL file with {"input": ..., "output": ...} pairs
            tokenizer_path: Path to trained SentencePiece .model file
            max_seq_len: Maximum sequence length (truncate longer examples)
            mask_instruction: If True, mask the instruction portion in labels
                              so the model only learns to predict the output.
        """
        self.max_seq_len = max_seq_len
        self.mask_instruction = mask_instruction

        # Load tokenizer
        self.tokenizer = spm.SentencePieceProcessor()
        self.tokenizer.load(str(tokenizer_path))
        self.pad_id = self.tokenizer.pad_id()
        self.bos_id = self.tokenizer.bos_id()
        self.eos_id = self.tokenizer.eos_id()

        # Load data
        self.examples = self._load_data(data_path)
        print(f"📊 Loaded {len(self.examples)} examples from {data_path}")

    def _load_data(self, data_path: str | Path) -> list[dict]:
        """Load JSONL data file."""
        data_path = Path(data_path)
        if not data_path.exists():
            raise FileNotFoundError(f"Data file not found: {data_path}")

        examples = []
        with open(data_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    example = json.loads(line)
                    if "input" in example and "output" in example:
                        examples.append(example)
        return examples

    def __len__(self) -> int:
        return len(self.examples)

    def __getitem__(self, idx: int) -> dict:
        """
        Returns a single tokenized example.

        Returns dict with:
            input_ids: (seq_len,) — token IDs
            labels: (seq_len,) — target IDs (-100 for masked positions)
            attention_mask: (seq_len,) — 1 for real tokens, 0 for padding
        """
        example = self.examples[idx]

        # Format the full instruction-following text
        full_text = INSTRUCTION_TEMPLATE.format(
            input_prompt=example["input"],
            output_prompt=example["output"],
        )

        # Tokenize
        token_ids = self.tokenizer.encode(full_text, out_type=int)

        # Truncate if too long
        if len(token_ids) > self.max_seq_len:
            token_ids = token_ids[:self.max_seq_len]

        # Create labels (same as input_ids for causal LM)
        labels = token_ids.copy()

        # Optionally mask the instruction portion so loss is only on the output
        if self.mask_instruction:
            # Find where "### Optimized Prompt:\n" ends in the tokenized sequence
            instruction_text = INFERENCE_TEMPLATE.format(input_prompt=example["input"])
            instruction_ids = self.tokenizer.encode(instruction_text, out_type=int)
            mask_len = min(len(instruction_ids), len(labels))

            # Set instruction portion to -100 (ignored in cross-entropy loss)
            for i in range(mask_len):
                labels[i] = -100

        return {
            "input_ids": torch.tensor(token_ids, dtype=torch.long),
            "labels": torch.tensor(labels, dtype=torch.long),
            "attention_mask": torch.ones(len(token_ids), dtype=torch.long),
        }


# ── Collate Function ──────────────────────────────────────────────────────────

def collate_fn(batch: list[dict], pad_id: int = 0) -> dict:
    """
    Collate function for DataLoader.
    Pads all sequences in the batch to the same length.

    Args:
        batch: List of dicts from PromptPairDataset.__getitem__
        pad_id: Token ID used for padding

    Returns:
        Batched tensors with padding applied.
    """
    max_len = max(item["input_ids"].size(0) for item in batch)

    input_ids = []
    labels = []
    attention_masks = []

    for item in batch:
        seq_len = item["input_ids"].size(0)
        pad_len = max_len - seq_len

        # Pad input_ids with pad_id
        input_ids.append(F.pad(item["input_ids"], (0, pad_len), value=pad_id))
        # Pad labels with -100 (ignored in loss)
        labels.append(F.pad(item["labels"], (0, pad_len), value=-100))
        # Pad attention mask with 0
        attention_masks.append(F.pad(item["attention_mask"], (0, pad_len), value=0))

    return {
        "input_ids": torch.stack(input_ids),
        "labels": torch.stack(labels),
        "attention_mask": torch.stack(attention_masks),
    }


# Need F for collate_fn
import torch.nn.functional as F


# ── Data Splitting ────────────────────────────────────────────────────────────

def create_data_splits(
    data_path: str | Path,
    output_dir: str | Path,
    train_ratio: float = 0.9,
    val_ratio: float = 0.05,
    test_ratio: float = 0.05,
    seed: int = 42,
):
    """
    Split a JSONL data file into train/val/test sets.

    Args:
        data_path: Input JSONL file
        output_dir: Directory to write split files
        train_ratio, val_ratio, test_ratio: Split ratios (must sum to 1.0)
        seed: Random seed for reproducibility
    """
    assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6, \
        "Split ratios must sum to 1.0"

    data_path = Path(data_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load all examples
    examples = []
    with open(data_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                examples.append(json.loads(line))

    # Shuffle with seed
    random.seed(seed)
    random.shuffle(examples)

    # Split
    n = len(examples)
    n_train = int(n * train_ratio)
    n_val = int(n * val_ratio)

    splits = {
        "train": examples[:n_train],
        "val": examples[n_train:n_train + n_val],
        "test": examples[n_train + n_val:],
    }

    # Write splits
    for split_name, split_data in splits.items():
        split_path = output_dir / f"{split_name}.jsonl"
        with open(split_path, "w", encoding="utf-8") as f:
            for example in split_data:
                f.write(json.dumps(example, ensure_ascii=False) + "\n")
        print(f"   📁 {split_name}: {len(split_data)} examples → {split_path}")


# ── DataLoader Factory ────────────────────────────────────────────────────────

def create_dataloader(
    data_path: str | Path,
    tokenizer_path: str | Path,
    batch_size: int = 8,
    max_seq_len: int = 1024,
    shuffle: bool = True,
    num_workers: int = 2,
    pin_memory: bool = True,
) -> DataLoader:
    """
    Create a ready-to-use DataLoader for training or evaluation.

    Args:
        data_path: JSONL file with prompt pairs
        tokenizer_path: SentencePiece model file
        batch_size: Batch size
        max_seq_len: Maximum sequence length
        shuffle: Shuffle data each epoch
        num_workers: DataLoader worker processes
        pin_memory: Pin memory for faster GPU transfer

    Returns:
        PyTorch DataLoader ready for the training loop
    """
    dataset = PromptPairDataset(
        data_path=data_path,
        tokenizer_path=tokenizer_path,
        max_seq_len=max_seq_len,
    )

    pad_id = dataset.pad_id

    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=num_workers,
        pin_memory=pin_memory,
        collate_fn=lambda batch: collate_fn(batch, pad_id=pad_id),
        drop_last=True,  # Drop last incomplete batch for training stability
    )


if __name__ == "__main__":
    print("📊 Dataset module loaded successfully.")
    print(f"   Instruction template length: {len(INSTRUCTION_TEMPLATE)} chars")
    print(f"   Inference template length: {len(INFERENCE_TEMPLATE)} chars")
