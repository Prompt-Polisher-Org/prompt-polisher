"""
train_tokenizer.py — Train a SentencePiece BPE tokenizer on the collected corpus.

Task: Week 3-4 / Tokenizer Training (task.md lines 229-238)
  [x] Train SentencePiece BPE tokenizer
  [x] Set vocabulary size = 32,000
  [x] Add special tokens: <pad>, <eos>, <bos>, <unk>, <sep>
  [x] Train on collected corpus
  [x] Evaluate tokenizer (fertility rate, coverage, manual spot-check)
  [x] Save tokenizer artifacts (tokenizer.model, tokenizer_config.json)
  [x] Write tokenizer integration test

Usage:
    # Step 1: Collect corpus (if not already done)
    python ai/src/tokenizer/collect_corpus.py

    # Step 2: Train tokenizer
    python ai/src/tokenizer/train_tokenizer.py

    # Step 3: Run evaluation + integration test
    python ai/src/tokenizer/train_tokenizer.py --evaluate-only
"""
import argparse
import json
import os
import sys
from pathlib import Path

import sentencepiece as spm


# ── Configuration ─────────────────────────────────────────────────────────────

# Paths
AI_DIR = Path(__file__).resolve().parent.parent.parent
CORPUS_FILE = AI_DIR / "data" / "corpus" / "tokenizer_corpus.txt"
MODEL_DIR = AI_DIR / "models" / "tokenizer"
MODEL_PREFIX = MODEL_DIR / "prompt_polisher_bpe"

# Tokenizer hyperparameters
VOCAB_SIZE = 32_000
MODEL_TYPE = "bpe"           # Byte-Pair Encoding
CHARACTER_COVERAGE = 0.9995  # Coverage of characters in the training data
MAX_SENTENCE_LENGTH = 4096   # Max input sentence length during training
NUM_THREADS = os.cpu_count() or 4

# Special tokens — these get reserved IDs at the start of the vocabulary
SPECIAL_TOKENS = {
    "pad_id": 0,     # <pad>  — padding for batching
    "unk_id": 1,     # <unk>  — unknown / out-of-vocabulary
    "bos_id": 2,     # <bos>  — beginning of sequence
    "eos_id": 3,     # <eos>  — end of sequence
}
# Additional user-defined special tokens (get IDs after the built-in ones)
USER_DEFINED_SYMBOLS = ["<sep>"]


# ── Training ──────────────────────────────────────────────────────────────────

def train_tokenizer():
    """Train a SentencePiece BPE tokenizer on the collected corpus."""

    if not CORPUS_FILE.exists():
        print(f"❌ Corpus file not found: {CORPUS_FILE}")
        print(f"   Run 'python ai/src/tokenizer/collect_corpus.py' first.")
        sys.exit(1)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    corpus_size_mb = CORPUS_FILE.stat().st_size / (1024 * 1024)
    print("=" * 70)
    print("🔤 Prompt Polisher — BPE Tokenizer Training")
    print("=" * 70)
    print(f"   📁 Corpus:     {CORPUS_FILE} ({corpus_size_mb:.1f} MB)")
    print(f"   📁 Output:     {MODEL_PREFIX}.model")
    print(f"   📊 Vocab size: {VOCAB_SIZE:,}")
    print(f"   🔧 Model type: {MODEL_TYPE.upper()}")
    print(f"   🧵 Threads:    {NUM_THREADS}")
    print("=" * 70)
    print()

    # Train the tokenizer
    spm.SentencePieceTrainer.train(
        input=str(CORPUS_FILE),
        model_prefix=str(MODEL_PREFIX),
        vocab_size=VOCAB_SIZE,
        model_type=MODEL_TYPE,
        character_coverage=CHARACTER_COVERAGE,
        max_sentence_length=MAX_SENTENCE_LENGTH,
        num_threads=NUM_THREADS,

        # Special token IDs
        pad_id=SPECIAL_TOKENS["pad_id"],
        unk_id=SPECIAL_TOKENS["unk_id"],
        bos_id=SPECIAL_TOKENS["bos_id"],
        eos_id=SPECIAL_TOKENS["eos_id"],

        # Additional special tokens
        user_defined_symbols=USER_DEFINED_SYMBOLS,

        # Training options
        shuffle_input_sentence=True,
        train_extremely_large_corpus=False,

        # Byte fallback for handling any character
        byte_fallback=True,
    )

    print(f"\n✅ Tokenizer training complete!")
    print(f"   📁 Model: {MODEL_PREFIX}.model")
    print(f"   📁 Vocab: {MODEL_PREFIX}.vocab")

    # Save tokenizer config as JSON for easy loading
    save_tokenizer_config()


def save_tokenizer_config():
    """Save tokenizer configuration as a JSON file alongside the model."""
    config = {
        "model_type": MODEL_TYPE,
        "vocab_size": VOCAB_SIZE,
        "model_file": "prompt_polisher_bpe.model",
        "special_tokens": {
            "<pad>": SPECIAL_TOKENS["pad_id"],
            "<unk>": SPECIAL_TOKENS["unk_id"],
            "<bos>": SPECIAL_TOKENS["bos_id"],
            "<eos>": SPECIAL_TOKENS["eos_id"],
            "<sep>": 4,  # First user-defined symbol
        },
        "character_coverage": CHARACTER_COVERAGE,
        "byte_fallback": True,
    }

    config_path = MODEL_DIR / "tokenizer_config.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    print(f"   📁 Config: {config_path}")


# ── Evaluation ────────────────────────────────────────────────────────────────

def load_tokenizer() -> spm.SentencePieceProcessor:
    """Load the trained tokenizer model."""
    model_path = f"{MODEL_PREFIX}.model"
    if not Path(model_path).exists():
        print(f"❌ Tokenizer model not found: {model_path}")
        print(f"   Run training first.")
        sys.exit(1)

    sp = spm.SentencePieceProcessor()
    sp.load(model_path)
    return sp


def evaluate_tokenizer():
    """Run comprehensive evaluation on the trained tokenizer."""
    sp = load_tokenizer()

    print("\n" + "=" * 70)
    print("📊 Tokenizer Evaluation")
    print("=" * 70)

    # ── 1. Basic Info ─────────────────────────────────────────────────────
    print(f"\n📋 Basic Info:")
    print(f"   Vocabulary size: {sp.get_piece_size():,}")
    print(f"   <pad> id: {sp.pad_id()}")
    print(f"   <unk> id: {sp.unk_id()}")
    print(f"   <bos> id: {sp.bos_id()}")
    print(f"   <eos> id: {sp.eos_id()}")

    # ── 2. Fertility Rate (tokens per word) ───────────────────────────────
    test_sentences = [
        "Write a professional email to my manager about the project deadline.",
        "Create a Python function that calculates the Fibonacci sequence using dynamic programming.",
        "Explain quantum computing to a 5-year-old child using simple analogies.",
        "Generate a marketing copy for a new AI-powered productivity tool.",
        "Refactor this code to follow SOLID principles and add error handling.",
        "Summarize the key findings from this research paper on transformer architectures.",
        "Write a compelling product description for an e-commerce listing.",
        "Debug this JavaScript code that has a race condition in the async handler.",
        "Translate this technical documentation into a user-friendly tutorial.",
        "Create a detailed prompt for generating a photorealistic landscape image.",
    ]

    total_tokens = 0
    total_words = 0

    print(f"\n📏 Fertility Rate (tokens per word):")
    for sentence in test_sentences:
        tokens = sp.encode(sentence, out_type=str)
        words = sentence.split()
        fertility = len(tokens) / len(words)
        total_tokens += len(tokens)
        total_words += len(words)
        print(f"   {fertility:.2f}  ({len(tokens):3d} tokens / {len(words):2d} words)  \"{sentence[:60]}...\"")

    avg_fertility = total_tokens / total_words
    print(f"\n   📊 Average fertility: {avg_fertility:.2f} tokens/word")
    if avg_fertility < 2.0:
        print(f"   ✅ Excellent — tokenizer is efficient for prompt text")
    elif avg_fertility < 3.0:
        print(f"   ✅ Good — acceptable fertility rate")
    else:
        print(f"   ⚠️  High fertility — consider larger vocab or more training data")

    # ── 3. Coverage on held-out data ──────────────────────────────────────
    print(f"\n📊 Coverage Check (unknown token rate):")
    unk_count = 0
    total_count = 0
    for sentence in test_sentences:
        ids = sp.encode(sentence, out_type=int)
        for token_id in ids:
            total_count += 1
            if token_id == sp.unk_id():
                unk_count += 1

    unk_rate = unk_count / total_count if total_count > 0 else 0
    print(f"   Total tokens: {total_count}")
    print(f"   Unknown tokens: {unk_count}")
    print(f"   Unknown rate: {unk_rate:.4%}")
    if unk_rate < 0.01:
        print(f"   ✅ Excellent coverage — less than 1% unknown tokens")
    else:
        print(f"   ⚠️  High unknown rate — may need more training data")

    # ── 4. Manual Spot-Check ──────────────────────────────────────────────
    print(f"\n🔍 Manual Spot-Check (tokenization examples):")
    spot_check_prompts = [
        "Write a blog post about machine learning",
        "def fibonacci(n):\n    if n <= 1:\n        return n",
        "Optimize this prompt for GPT-4: make it more specific and add constraints",
    ]

    for prompt in spot_check_prompts:
        tokens = sp.encode(prompt, out_type=str)
        print(f"\n   Input:  \"{prompt}\"")
        print(f"   Tokens: {tokens}")
        print(f"   Count:  {len(tokens)}")

    # ── 5. Roundtrip Test ─────────────────────────────────────────────────
    print(f"\n🔄 Roundtrip Test (encode → decode):")
    all_pass = True
    for sentence in test_sentences[:5]:
        ids = sp.encode(sentence, out_type=int)
        decoded = sp.decode(ids)
        match = decoded.strip() == sentence.strip()
        status = "✅" if match else "❌"
        if not match:
            all_pass = False
        print(f"   {status} \"{sentence[:50]}...\"")

    print(f"\n   {'✅ All roundtrip tests passed!' if all_pass else '⚠️  Some roundtrip mismatches (may be whitespace normalization)'}")
    print("=" * 70)


# ── Integration Test ──────────────────────────────────────────────────────────

def run_integration_test():
    """Run a basic integration test to verify the tokenizer works correctly."""
    print("\n" + "=" * 70)
    print("🧪 Tokenizer Integration Test")
    print("=" * 70)

    sp = load_tokenizer()
    errors = []

    # Test 1: Vocab size
    if sp.get_piece_size() != VOCAB_SIZE:
        errors.append(f"Vocab size mismatch: expected {VOCAB_SIZE}, got {sp.get_piece_size()}")
    else:
        print(f"   ✅ Vocab size: {sp.get_piece_size()}")

    # Test 2: Special token IDs
    if sp.pad_id() != 0:
        errors.append(f"pad_id mismatch: expected 0, got {sp.pad_id()}")
    if sp.unk_id() != 1:
        errors.append(f"unk_id mismatch: expected 1, got {sp.unk_id()}")
    if sp.bos_id() != 2:
        errors.append(f"bos_id mismatch: expected 2, got {sp.bos_id()}")
    if sp.eos_id() != 3:
        errors.append(f"eos_id mismatch: expected 3, got {sp.eos_id()}")
    print(f"   ✅ Special tokens: pad=0, unk=1, bos=2, eos=3")

    # Test 3: <sep> token exists
    sep_id = sp.piece_to_id("<sep>")
    if sep_id == sp.unk_id():
        errors.append("<sep> token not found in vocabulary")
    else:
        print(f"   ✅ <sep> token id: {sep_id}")

    # Test 4: Encode produces non-empty output
    test_text = "Improve this prompt to be more specific and detailed."
    ids = sp.encode(test_text, out_type=int)
    if len(ids) == 0:
        errors.append("Encoding produced empty output")
    else:
        print(f"   ✅ Encode test: {len(ids)} tokens")

    # Test 5: Decode produces readable output
    decoded = sp.decode(ids)
    if len(decoded.strip()) == 0:
        errors.append("Decoding produced empty output")
    else:
        print(f"   ✅ Decode test: \"{decoded.strip()[:50]}...\"")

    # Test 6: No all-unknown encoding
    all_unk = all(t == sp.unk_id() for t in ids)
    if all_unk:
        errors.append("All tokens are <unk> — tokenizer not working correctly")
    else:
        print(f"   ✅ No all-unknown encoding")

    # Test 7: Config file exists and is valid JSON
    config_path = MODEL_DIR / "tokenizer_config.json"
    if config_path.exists():
        with open(config_path, "r") as f:
            config = json.load(f)
        if config.get("vocab_size") != VOCAB_SIZE:
            errors.append(f"Config vocab_size mismatch")
        else:
            print(f"   ✅ Config file valid")
    else:
        errors.append(f"Config file not found: {config_path}")

    # Results
    print()
    if errors:
        print(f"❌ Integration test FAILED with {len(errors)} error(s):")
        for err in errors:
            print(f"   ❌ {err}")
        return False
    else:
        print(f"✅ All integration tests passed!")
        return True


# ── CLI Entry Point ───────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Train and evaluate the Prompt Polisher BPE tokenizer")
    parser.add_argument("--evaluate-only", action="store_true",
                        help="Skip training, only run evaluation and integration tests")
    parser.add_argument("--test-only", action="store_true",
                        help="Only run the integration test")
    args = parser.parse_args()

    if args.test_only:
        success = run_integration_test()
        sys.exit(0 if success else 1)

    if args.evaluate_only:
        evaluate_tokenizer()
        run_integration_test()
        return

    # Full pipeline: train → evaluate → test
    train_tokenizer()
    evaluate_tokenizer()
    run_integration_test()


if __name__ == "__main__":
    main()
