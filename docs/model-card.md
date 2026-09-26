# PromptPolisherTransformer — Model Card

## Model Overview

| Property | Value |
|----------|-------|
| **Model Name** | PromptPolisherTransformer |
| **Type** | Causal Decoder-Only Transformer (autoregressive language model) |
| **Task** | Prompt Optimization — transforms raw, unoptimized prompts into effective, detailed prompts |
| **Parameters** | ~22.9M (Small) / ~42.1M (Base) / ~110M (Large) |
| **Trained Variant** | Small (22.9M) |
| **Framework** | PyTorch (custom implementation, no HuggingFace dependency) |
| **License** | MIT |

---

## Architecture

The model follows **LLaMA-style** modern Transformer conventions, purpose-built for the prompt optimization task.

### Core Components

| Component | Implementation | Rationale |
|-----------|---------------|-----------|
| **Normalization** | RMSNorm (pre-norm) | Simpler and faster than LayerNorm; no mean subtraction or bias needed |
| **Attention** | Multi-Head Causal Self-Attention | Standard autoregressive attention with causal masking |
| **Positional Encoding** | Rotary Position Embeddings (RoPE) | Better length generalization than learned/sinusoidal embeddings |
| **Feed-Forward** | SwiGLU activation (gate + up + down projections) | Superior performance over ReLU/GELU in modern LLMs |
| **Residual Connections** | Pre-norm residual (add after norm → attention/FFN) | Stabilizes deep network training |
| **Output Head** | Tied with token embeddings | Reduces parameter count and improves performance |

### Configuration Presets

| Preset | Layers | Hidden Dim | Heads | FFN Dim | Context | Parameters |
|--------|--------|-----------|-------|---------|---------|-----------|
| **Small** | 6 | 384 | 6 | 1,024 | 512 | ~22.9M |
| **Base** | 8 | 512 | 8 | 1,408 | 1,024 | ~42.1M |
| **Large** | 12 | 768 | 12 | 2,048 | 2,048 | ~110M |

### Architecture Diagram

```
Input Tokens
    │
    ▼
┌─────────────────────┐
│  Token Embedding     │  (vocab_size × hidden_dim)
│  + RoPE Positions    │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Transformer Block   │ × N layers
│  ┌─────────────────┐ │
│  │ RMSNorm         │ │
│  │ Multi-Head Attn │ │ (Q, K, V projections + RoPE + causal mask)
│  │ + Residual      │ │
│  ├─────────────────┤ │
│  │ RMSNorm         │ │
│  │ SwiGLU FFN      │ │ (gate_proj ⊙ SiLU(up_proj)) → down_proj
│  │ + Residual      │ │
│  └─────────────────┘ │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Final RMSNorm       │
│  Linear Output Head  │ → logits (vocab_size)
└─────────────────────┘
```

---

## Training Data

### Phase 1: Supervised Fine-Tuning (SFT)

| Property | Value |
|----------|-------|
| **Dataset Size** | 5,000 – 10,000 (input_prompt → optimized_prompt) pairs |
| **Data Sources** | Databricks Dolly-15k, Stanford Alpaca, Code Alpaca |
| **Format** | Instruction-tuning template with `<bos>` / `<eos>` markers |
| **Split** | 90% train / 5% validation / 5% test |
| **Deduplication** | By lowercase input prompt |

**Instruction Template:**
```
<bos>### Instruction:
Optimize the following prompt to be more effective, specific, and detailed.

### Input Prompt:
{input_prompt}

### Optimized Prompt:
{output_prompt}<eos>
```

### Phase 2: Direct Preference Optimization (DPO)

| Property | Value |
|----------|-------|
| **Dataset** | (prompt, chosen, rejected) triples from user feedback |
| **Source** | RLHF feedback pipeline — thumbs up = chosen, thumbs down = rejected |
| **Beta (KL penalty)** | 0.1 |
| **Learning Rate** | 5e-6 (lower than SFT to prevent catastrophic forgetting) |
| **Steps** | 2,000 |

### Tokenizer

| Property | Value |
|----------|-------|
| **Algorithm** | SentencePiece BPE (Byte Pair Encoding) |
| **Vocabulary Size** | 32,000 tokens |
| **Special Tokens** | `<pad>`, `<unk>`, `<bos>`, `<eos>` |
| **Training Corpus** | Same datasets as SFT data |
| **Average Fertility** | ~1.5 tokens/word (efficient for English prompt text) |

---

## Training Details

### SFT Training

| Hyperparameter | Value |
|---------------|-------|
| **Optimizer** | AdamW (β₁=0.9, β₂=0.95) |
| **Peak Learning Rate** | 3e-4 |
| **LR Schedule** | Cosine decay with linear warmup |
| **Warmup Steps** | 500 |
| **Total Steps** | 50,000 |
| **Batch Size** | 8 × 4 gradient accumulation = 32 effective |
| **Precision** | Mixed (FP16) |
| **Gradient Clipping** | Max norm 1.0 |
| **Weight Decay** | 0.01 |
| **Hardware** | NVIDIA Tesla T4 (Google Colab) |

### DPO Training

| Hyperparameter | Value |
|---------------|-------|
| **Optimizer** | AdamW (β₁=0.9, β₂=0.95) |
| **Learning Rate** | 5e-6 |
| **Beta** | 0.1 |
| **Total Steps** | 2,000 |
| **Batch Size** | 2 |
| **Reference Model** | Frozen SFT checkpoint |

---

## Evaluation

### Metrics Supported

| Metric | Description |
|--------|-------------|
| **Perplexity** | exp(avg cross-entropy loss) on held-out test set. Lower = better. |
| **BLEU** | N-gram overlap between generated and reference optimized prompts. |
| **ROUGE-L** | Longest Common Subsequence F1 between generated and reference. |
| **Manual Evaluation** | 20 sample prompt generations for qualitative human review. |

### How to Run Evaluation

```bash
python -m ai.src.training.evaluate --checkpoint ai/models/checkpoints/best_model.pt --num-samples 20
```

This outputs perplexity, BLEU, ROUGE-L, and generates 20 sample optimized prompts for manual inspection.

---

## Inference

### REST API
```bash
curl -X POST http://localhost:8001/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Write about dogs", "max_new_tokens": 256, "temperature": 0.7}'
```

### Generation Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_new_tokens` | 256 | Maximum tokens to generate |
| `temperature` | 0.7 | Sampling temperature (0 = greedy, 1 = more random) |
| `top_k` | 50 | Top-K sampling filter |
| `top_p` | 0.9 | Nucleus sampling threshold |

---

## Limitations & Known Issues

1. **Small Training Corpus:** The SFT dataset (5K-10K pairs) is relatively small. The model may struggle with highly specialized domains not represented in Dolly/Alpaca (e.g., medical, legal).

2. **English Only:** The tokenizer and training data are English-centric. Non-English prompts will produce poor results.

3. **Context Window:** The Small model is limited to 512 tokens. Very long prompts will be truncated.

4. **Hallucination Risk:** Like all autoregressive language models, the model may occasionally generate plausible-sounding but factually incorrect prompt suggestions.

5. **DPO Data Scarcity:** The DPO phase was trained on a very small feedback dataset. More user feedback would significantly improve preference alignment.

6. **No Safety Filtering:** The model does not include content safety filtering. It may generate prompts for harmful use cases if the input prompt is adversarial.

---

## Ethical Considerations

- The model is designed to **improve prompt quality**, not to generate original content. Its outputs are always meant to be used as inputs to other LLMs.
- No personally identifiable information (PII) is stored in the model weights.
- User feedback data used for DPO is anonymized before training.
- The system includes rate limiting and authentication to prevent abuse.

---

## File Structure

```
ai/
├── models/
│   ├── checkpoints/
│   │   ├── best_model.pt        # SFT best checkpoint
│   │   └── dpo/
│   │       ├── dpo_best.pt      # DPO best checkpoint
│   │       └── dpo_final.pt     # DPO final checkpoint
│   └── tokenizer/
│       └── prompt_polisher_bpe.model  # SentencePiece tokenizer
├── src/
│   ├── training/
│   │   ├── architecture.py      # Model definition
│   │   ├── config.py            # Model configurations
│   │   ├── dataset.py           # Data loading & collation
│   │   ├── train.py             # SFT training loop
│   │   ├── dpo_trainer.py       # DPO training loop
│   │   ├── evaluate.py          # Evaluation metrics
│   │   └── collect_sft_data.py  # Dataset collection
│   ├── tokenizer/
│   │   ├── train_tokenizer.py   # BPE tokenizer training
│   │   └── collect_corpus.py    # Corpus collection
│   └── inference/
│       └── server.py            # FastAPI inference server
```

---

## Reproduction Instructions

### Step 1: Train the Tokenizer
```bash
python -m ai.src.tokenizer.collect_corpus
python -m ai.src.tokenizer.train_tokenizer
```

### Step 2: Collect SFT Data
```bash
python -m ai.src.training.collect_sft_data
```

### Step 3: Run SFT Training
```bash
python -m ai.src.training.train
```

### Step 4: Run DPO Training (after collecting user feedback)
```bash
python -m ai.src.training.dpo_trainer \
    --base_checkpoint ai/models/checkpoints/best_model.pt \
    --feedback_data ai/data/feedback/dpo_triples.jsonl \
    --config small
```

### Step 5: Evaluate
```bash
python -m ai.src.training.evaluate --checkpoint ai/models/checkpoints/best_model.pt
```
