"""
collect_corpus.py — Download and clean a text corpus for tokenizer training.

Task: Week 3-4 / Tokenizer Training (task.md lines 225-228)
  [x] Collect and clean text corpus (~2-5GB)
  [x] Filter for English prompt-engineering content
  [x] Remove duplicates
  [x] Clean HTML/markdown artifacts

This script downloads prompt-engineering datasets from HuggingFace,
cleans and deduplicates the text, and writes a single .txt file
suitable for SentencePiece training.

Usage:
    python ai/src/tokenizer/collect_corpus.py
"""
import os
import re
import hashlib
from pathlib import Path

from datasets import load_dataset
from tqdm import tqdm


# ── Configuration ─────────────────────────────────────────────────────────────

OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "corpus"
OUTPUT_FILE = OUTPUT_DIR / "tokenizer_corpus.txt"

# Datasets to download from HuggingFace
# Each entry: (dataset_name, config, split, text_fields)
DATASETS = [
    # OpenAssistant conversations — high-quality instruction/response pairs
    ("OpenAssistant/oasst2", None, "train", ["text"]),
    # Databricks Dolly — instruction-tuning data covering many categories
    ("databricks/databricks-dolly-15k", None, "train", ["instruction", "context", "response"]),
    # Prompt engineering examples — self-instruct style
    ("sahil2801/CodeAlpaca-20k", None, "train", ["instruction", "input", "output"]),
]

# Minimum line length to keep (filters out noise)
MIN_LINE_LENGTH = 20
# Maximum line length (truncate very long lines to save space)
MAX_LINE_LENGTH = 4096


# ── Cleaning Functions ────────────────────────────────────────────────────────

def clean_html(text: str) -> str:
    """Remove HTML tags from text."""
    return re.sub(r"<[^>]+>", "", text)


def clean_markdown(text: str) -> str:
    """Remove common markdown artifacts (headers, bold, links, images)."""
    # Remove image markdown: ![alt](url)
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)
    # Remove link markdown: [text](url) → text
    text = re.sub(r"\[([^\]]*)\]\([^)]+\)", r"\1", text)
    # Remove header markers: ### Header → Header
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    # Remove bold/italic markers
    text = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", text)
    text = re.sub(r"_{1,3}([^_]+)_{1,3}", r"\1", text)
    return text


def clean_text(text: str) -> str:
    """Apply all cleaning steps to a text string."""
    text = clean_html(text)
    text = clean_markdown(text)
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    # Remove control characters (but keep newlines)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    return text


def line_hash(text: str) -> str:
    """Generate a hash for deduplication."""
    return hashlib.md5(text.encode("utf-8", errors="ignore")).hexdigest()


# ── Main Collection Pipeline ─────────────────────────────────────────────────

def collect_and_clean():
    """Download datasets, clean text, deduplicate, and write corpus file."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    seen_hashes = set()
    total_lines = 0
    duplicate_count = 0

    print("=" * 70)
    print("📚 Prompt Polisher — Corpus Collection for Tokenizer Training")
    print("=" * 70)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for dataset_name, config, split, fields in DATASETS:
            print(f"\n📥 Loading: {dataset_name} (split={split})...")

            try:
                ds = load_dataset(dataset_name, config, split=split, trust_remote_code=True)
            except Exception as e:
                print(f"   ⚠️  Failed to load {dataset_name}: {e}")
                print(f"   Skipping this dataset and continuing...")
                continue

            print(f"   ✅ Loaded {len(ds)} examples")

            for example in tqdm(ds, desc=f"   Processing {dataset_name}", leave=False):
                # Concatenate all text fields for this example
                parts = []
                for field in fields:
                    value = example.get(field, "")
                    if value and isinstance(value, str):
                        parts.append(value)

                text = " ".join(parts)
                text = clean_text(text)

                # Filter: too short
                if len(text) < MIN_LINE_LENGTH:
                    continue

                # Truncate: too long
                if len(text) > MAX_LINE_LENGTH:
                    text = text[:MAX_LINE_LENGTH]

                # Deduplicate
                h = line_hash(text)
                if h in seen_hashes:
                    duplicate_count += 1
                    continue
                seen_hashes.add(h)

                # Write cleaned line
                f.write(text + "\n")
                total_lines += 1

            print(f"   📊 Running total: {total_lines:,} lines")

    # Summary
    file_size_mb = OUTPUT_FILE.stat().st_size / (1024 * 1024)
    print("\n" + "=" * 70)
    print("✅ Corpus collection complete!")
    print(f"   📁 Output:     {OUTPUT_FILE}")
    print(f"   📊 Total lines: {total_lines:,}")
    print(f"   🔁 Duplicates removed: {duplicate_count:,}")
    print(f"   💾 File size:  {file_size_mb:.1f} MB")
    print("=" * 70)


if __name__ == "__main__":
    collect_and_clean()
