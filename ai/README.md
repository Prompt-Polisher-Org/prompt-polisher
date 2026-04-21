# 🤖 AI — Model Training, Inference & RAG

> **Tech Stack**: PyTorch 2.x · HuggingFace Transformers · SentencePiece · Sentence-Transformers · TRL (DPO) · Qdrant

## Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
jupyter lab                    # For experimentation
```

## Directory Structure

```
ai/
├── tokenizer/
│   ├── train_tokenizer.py     # Train SentencePiece BPE tokenizer
│   └── tokenizer_config.json
├── model/
│   ├── config.py              # Model hyperparameters
│   ├── architecture.py        # Custom transformer architecture
│   ├── dataset.py             # Dataset loading & preprocessing
│   ├── train.py               # Pre-training / SFT script
│   └── evaluate.py            # Evaluation metrics
├── rlhf/
│   ├── ppo_trainer.py         # DPO/PPO training loop
│   └── data_pipeline.py       # Feedback data preprocessing
├── inference/
│   ├── engine.py              # Inference engine with KV-cache
│   ├── server.py              # Inference HTTP server
│   └── quantize.py            # INT8 quantization
├── rag/
│   ├── embedder.py            # Sentence-transformer wrapper
│   ├── retriever.py           # Qdrant retrieval logic
│   └── augmenter.py           # Context injection
├── data/
│   ├── raw/                   # Raw datasets (git-ignored)
│   ├── processed/             # Processed data (git-ignored)
│   └── feedback/              # RLHF feedback logs
├── notebooks/                 # Jupyter notebooks
└── requirements.txt
```

## Owner
🤖 **AI / Model Architect** (Member B)
