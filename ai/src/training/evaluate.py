"""
evaluate.py — Evaluate the trained Prompt Polisher model.

Task: Week 5-6 / Model Architecture (task.md lines 287-290)
  [x] Calculate perplexity on test set
  [x] Calculate BLEU/ROUGE on prompt optimization
  [x] Manual evaluation: generate 20 sample outputs

Usage:
    python ai/src/training/evaluate.py --checkpoint ai/models/checkpoints/best_model.pt
"""
import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path

import torch
import sentencepiece as spm

from ai.src.training.config import ModelConfig
from ai.src.training.architecture import PromptPolisherTransformer
from ai.src.training.dataset import create_dataloader, INFERENCE_TEMPLATE


# ── Perplexity ────────────────────────────────────────────────────────────────

@torch.no_grad()
def calculate_perplexity(model, dataloader, device) -> float:
    """
    Calculate perplexity on a dataset.
    Perplexity = exp(average cross-entropy loss).
    Lower is better. A perplexity of N means the model is as uncertain
    as if it were choosing uniformly among N tokens.
    """
    model.eval()
    total_loss = 0.0
    total_tokens = 0

    for batch in dataloader:
        input_ids = batch["input_ids"].to(device)
        labels = batch["labels"].to(device)

        output = model(input_ids, labels=labels)
        # Count non-masked tokens in labels
        num_tokens = (labels[:, 1:] != -100).sum().item()
        total_loss += output["loss"].item() * num_tokens
        total_tokens += num_tokens

    avg_loss = total_loss / max(1, total_tokens)
    perplexity = math.exp(avg_loss)
    return perplexity


# ── BLEU Score (Simple Implementation) ────────────────────────────────────────

def get_ngrams(tokens: list, n: int) -> Counter:
    """Extract n-grams from a token list."""
    return Counter(tuple(tokens[i:i+n]) for i in range(len(tokens) - n + 1))


def compute_bleu(reference: str, hypothesis: str, max_n: int = 4) -> float:
    """
    Compute BLEU score between reference and hypothesis.
    Simple implementation without brevity penalty smoothing.
    """
    ref_tokens = reference.lower().split()
    hyp_tokens = hypothesis.lower().split()

    if len(hyp_tokens) == 0:
        return 0.0

    # Brevity penalty
    bp = min(1.0, math.exp(1 - len(ref_tokens) / max(1, len(hyp_tokens))))

    # N-gram precisions
    precisions = []
    for n in range(1, max_n + 1):
        ref_ngrams = get_ngrams(ref_tokens, n)
        hyp_ngrams = get_ngrams(hyp_tokens, n)

        matches = 0
        total = 0
        for ngram, count in hyp_ngrams.items():
            matches += min(count, ref_ngrams.get(ngram, 0))
            total += count

        if total == 0:
            precisions.append(0.0)
        else:
            precisions.append(matches / total)

    # Geometric mean of precisions (with smoothing for zero precisions)
    log_avg = 0.0
    for p in precisions:
        if p > 0:
            log_avg += math.log(p) / max_n
        else:
            return 0.0  # If any precision is 0, BLEU is 0

    return bp * math.exp(log_avg)


# ── ROUGE-L Score ─────────────────────────────────────────────────────────────

def lcs_length(x: list, y: list) -> int:
    """Compute length of Longest Common Subsequence."""
    m, n = len(x), len(y)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if x[i-1] == y[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    return dp[m][n]


def compute_rouge_l(reference: str, hypothesis: str) -> float:
    """Compute ROUGE-L F1 score between reference and hypothesis."""
    ref_tokens = reference.lower().split()
    hyp_tokens = hypothesis.lower().split()

    if len(ref_tokens) == 0 or len(hyp_tokens) == 0:
        return 0.0

    lcs = lcs_length(ref_tokens, hyp_tokens)
    precision = lcs / len(hyp_tokens)
    recall = lcs / len(ref_tokens)

    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


# ── Generate Samples ──────────────────────────────────────────────────────────

@torch.no_grad()
def generate_samples(
    model,
    tokenizer,
    prompts: list[str],
    device,
    max_new_tokens: int = 256,
    temperature: float = 0.7,
) -> list[str]:
    """Generate optimized prompts for a list of input prompts."""
    model.eval()
    results = []

    for prompt in prompts:
        # Format using inference template
        formatted = INFERENCE_TEMPLATE.format(input_prompt=prompt)

        # Tokenize
        input_ids = tokenizer.encode(formatted, out_type=int)
        input_tensor = torch.tensor([input_ids], dtype=torch.long).to(device)

        # Generate
        output_ids = model.generate(
            input_tensor,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_k=50,
            top_p=0.9,
            eos_token_id=tokenizer.eos_id(),
        )

        # Decode only the generated part
        generated_ids = output_ids[0, len(input_ids):].tolist()
        generated_text = tokenizer.decode(generated_ids)

        results.append(generated_text.strip())

    return results


# ── Full Evaluation ───────────────────────────────────────────────────────────

def evaluate(checkpoint_path: str, num_samples: int = 20):
    """Run full evaluation suite on a checkpoint."""

    # ── Load checkpoint ───────────────────────────────────────────────────
    print("=" * 70)
    print("📊 Prompt Polisher — Model Evaluation")
    print("=" * 70)

    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    config = ModelConfig(**checkpoint["config"])
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    print(f"\n📂 Checkpoint: {checkpoint_path}")
    print(f"   Step: {checkpoint['step']}")
    print(f"   Training loss: {checkpoint['loss']:.4f}")
    print(f"   Device: {device}")
    print(f"\n{config}")

    # Create model and load weights
    model = PromptPolisherTransformer(config)
    model.load_state_dict(checkpoint["model_state_dict"])
    model = model.to(device)
    model.eval()

    # Load tokenizer
    tokenizer = spm.SentencePieceProcessor()
    tokenizer.load(config.tokenizer_model)

    # ── 1. Perplexity ─────────────────────────────────────────────────────
    test_data_path = Path(config.data_dir) / "sft" / "splits" / "test.jsonl"
    if test_data_path.exists():
        print(f"\n📏 Calculating perplexity on test set...")
        import os
        test_loader = create_dataloader(
            data_path=test_data_path,
            tokenizer_path=config.tokenizer_model,
            batch_size=config.batch_size,
            max_seq_len=config.max_seq_len,
            shuffle=False,
            num_workers=0 if os.name == "nt" else 2,
        )
        ppl = calculate_perplexity(model, test_loader, device)
        print(f"   📊 Perplexity: {ppl:.2f}")
        if ppl < 20:
            print(f"   ✅ Excellent perplexity")
        elif ppl < 50:
            print(f"   ✅ Good perplexity")
        else:
            print(f"   ⚠️  High perplexity — model may need more training")
    else:
        print(f"\n⚠️  Test set not found: {test_data_path}")

    # ── 2. BLEU & ROUGE on test examples ──────────────────────────────────
    if test_data_path.exists():
        print(f"\n📏 Calculating BLEU & ROUGE-L...")
        test_examples = []
        with open(test_data_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    test_examples.append(json.loads(line))

        # Use up to 100 examples for BLEU/ROUGE
        eval_examples = test_examples[:100]
        input_prompts = [ex["input"] for ex in eval_examples]
        reference_outputs = [ex["output"] for ex in eval_examples]

        # Generate outputs
        print(f"   Generating {len(input_prompts)} outputs...")
        generated_outputs = generate_samples(model, tokenizer, input_prompts, device)

        # Calculate metrics
        bleu_scores = []
        rouge_scores = []
        for ref, hyp in zip(reference_outputs, generated_outputs):
            bleu_scores.append(compute_bleu(ref, hyp))
            rouge_scores.append(compute_rouge_l(ref, hyp))

        avg_bleu = sum(bleu_scores) / len(bleu_scores)
        avg_rouge = sum(rouge_scores) / len(rouge_scores)

        print(f"   📊 Average BLEU:    {avg_bleu:.4f}")
        print(f"   📊 Average ROUGE-L: {avg_rouge:.4f}")

    # ── 3. Manual Evaluation — Generate 20 samples ────────────────────────
    print(f"\n🔍 Manual Evaluation — Generating {num_samples} sample outputs...")
    print("=" * 70)

    sample_prompts = [
        "Write about dogs",
        "Explain machine learning",
        "Create a marketing email",
        "Help me with Python code",
        "Summarize this article",
        "Write a story",
        "Generate SQL query",
        "Create a workout plan",
        "Explain blockchain",
        "Write a cover letter",
        "Debug this code",
        "Create a recipe",
        "Explain quantum physics",
        "Write product description",
        "Create a study plan",
        "Help with data analysis",
        "Write a poem",
        "Explain HTTPS",
        "Create a business plan",
        "Write interview questions",
    ][:num_samples]

    generated = generate_samples(model, tokenizer, sample_prompts, device)

    # Save results
    results_dir = Path(config.checkpoint_dir) / "evaluation"
    results_dir.mkdir(parents=True, exist_ok=True)
    results_file = results_dir / "sample_outputs.json"

    results = []
    for prompt, output in zip(sample_prompts, generated):
        result = {"input": prompt, "generated_output": output}
        results.append(result)
        print(f"\n{'─'*60}")
        print(f"  INPUT:    {prompt}")
        print(f"  OUTPUT:   {output[:200]}{'...' if len(output) > 200 else ''}")

    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n{'─'*60}")
    print(f"\n📁 Results saved: {results_file}")
    print("=" * 70)
    print("✅ Evaluation complete!")
    print("=" * 70)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Evaluate the Prompt Polisher model")
    parser.add_argument("--checkpoint", type=str, required=True,
                        help="Path to model checkpoint (.pt file)")
    parser.add_argument("--num-samples", type=int, default=20,
                        help="Number of sample outputs to generate")
    args = parser.parse_args()

    if not Path(args.checkpoint).exists():
        print(f"❌ Checkpoint not found: {args.checkpoint}")
        sys.exit(1)

    evaluate(args.checkpoint, num_samples=args.num_samples)


if __name__ == "__main__":
    main()
