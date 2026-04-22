# 🤖 AI Module — Prompt Polisher

Model training, inference, and RAG pipeline for the Prompt Polisher platform.

## Tech Stack

| Package | Version | Purpose |
|---|---|---|
| Python | 3.12.4 | Runtime |
| PyTorch | 2.5.1+cu121 | Deep learning framework (CUDA 12.1) |
| Transformers | 5.5.4 | HuggingFace model hub & fine-tuning |
| Datasets | 4.8.4 | Dataset loading & preprocessing |
| TRL | 1.2.0 | RLHF / SFT / DPO training |
| SentencePiece | — | Tokenizer backend |
| Sentence-Transformers | 5.4.1 | Embedding models for RAG |
| JupyterLab | — | Notebook environment |

## Environment Setup

```bash
# 1. Create virtual environment (requires Python 3.12)
py -3.12 -m venv venv

# 2. Activate
# Windows
.\venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 3. Install PyTorch with CUDA 12.1
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 4. Install AI dependencies
pip install transformers datasets trl sentencepiece sentence-transformers jupyterlab

# 5. Verify installation
python -c "import torch; print(f'PyTorch {torch.__version__}, CUDA: {torch.cuda.is_available()}')"
```

> **Note**: PyTorch does NOT support Python 3.13 yet. You must use Python 3.11 or 3.12.

## Launch Jupyter Lab

```bash
jupyter lab --port=8888
```

## Project Structure

```
ai/
├── data/               # Raw & processed datasets
├── models/             # Saved model checkpoints
├── notebooks/          # Jupyter notebooks for experimentation
├── src/                # Training & inference source code
│   ├── training/       # SFT, DPO, RLHF scripts
│   ├── inference/      # Model serving & API
│   └── embeddings/     # RAG embedding pipeline
├── requirements.txt    # Frozen dependencies
└── README.md           # This file
```

## Dataset Strategy

### Target Datasets
| Dataset | Source | Purpose |
|---|---|---|
| ShareGPT | HuggingFace | Multi-turn conversation examples |
| LMSYS-Chat-1M | HuggingFace | Prompt quality & preference data |
| OpenAssistant | HuggingFace | Instruction-following pairs |
| Anthropic HH-RLHF | HuggingFace | Human preference for RLHF |
| Custom Web Scrapes | APIs / Scraping | Domain-specific prompt patterns |

### Licensing
All datasets must be verified for licensing compatibility before use. Document licenses in `data/LICENSE_REGISTRY.md`.
