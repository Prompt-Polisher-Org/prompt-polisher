"""
architecture.py — Custom Transformer decoder for Prompt Polisher.

Task: Week 5-6 / Model Architecture (task.md lines 260-265)
  [x] Token + positional embeddings
  [x] Multi-head self-attention with causal mask
  [x] Feed-forward network (SwiGLU activation)
  [x] RMSNorm
  [x] Residual connections

Architecture follows modern LLM conventions (LLaMA-style):
- RMSNorm (pre-norm) instead of LayerNorm
- SwiGLU activation in FFN instead of ReLU/GELU
- Rotary Position Embeddings (RoPE) for better length generalization
- Causal (autoregressive) attention mask
"""
import math
from typing import Optional

import torch
import torch.nn as nn
import torch.nn.functional as F

from ai.src.training.config import ModelConfig


# ── RMSNorm ───────────────────────────────────────────────────────────────────

class RMSNorm(nn.Module):
    """
    Root Mean Square Layer Normalization.
    Simpler and faster than LayerNorm — no mean subtraction or bias.
    Used in LLaMA, Gemma, and other modern architectures.
    """

    def __init__(self, dim: int, eps: float = 1e-6):
        super().__init__()
        self.eps = eps
        self.weight = nn.Parameter(torch.ones(dim))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # RMS = sqrt(mean(x^2))
        rms = torch.sqrt(x.pow(2).mean(-1, keepdim=True) + self.eps)
        return x / rms * self.weight


# ── Rotary Position Embeddings (RoPE) ─────────────────────────────────────────

def precompute_rope_frequencies(dim: int, max_seq_len: int, base: float = 10000.0) -> torch.Tensor:
    """
    Precompute the complex rotation frequencies for RoPE.
    Returns a tensor of shape (max_seq_len, dim // 2) with complex values.
    """
    # Frequency for each dimension pair
    freqs = 1.0 / (base ** (torch.arange(0, dim, 2).float() / dim))
    # Position indices
    t = torch.arange(max_seq_len).float()
    # Outer product: (seq_len, dim//2)
    freqs = torch.outer(t, freqs)
    # Convert to complex: e^(i*theta) = cos(theta) + i*sin(theta)
    return torch.polar(torch.ones_like(freqs), freqs)


def apply_rope(x: torch.Tensor, rope_freqs: torch.Tensor) -> torch.Tensor:
    """
    Apply rotary position embeddings to query or key tensors.
    x: (batch, seq_len, num_heads, head_dim)
    rope_freqs: (seq_len, head_dim // 2)
    """
    # Reshape x into pairs of (x1, x2) and treat as complex numbers
    x_complex = torch.view_as_complex(x.float().reshape(*x.shape[:-1], -1, 2))
    # Reshape freqs for broadcasting: (1, seq_len, 1, head_dim//2)
    rope_freqs = rope_freqs.unsqueeze(0).unsqueeze(2)
    # Multiply complex numbers = rotate in 2D plane
    x_rotated = torch.view_as_real(x_complex * rope_freqs).flatten(-2)
    return x_rotated.type_as(x)


# ── Multi-Head Causal Self-Attention ──────────────────────────────────────────

class CausalSelfAttention(nn.Module):
    """
    Multi-head self-attention with causal (autoregressive) masking.
    Uses RoPE for position information instead of absolute position embeddings.
    """

    def __init__(self, config: ModelConfig):
        super().__init__()
        self.num_heads = config.num_heads
        self.head_dim = config.head_dim
        self.hidden_dim = config.hidden_dim

        # Q, K, V projections (combined for efficiency)
        self.q_proj = nn.Linear(config.hidden_dim, config.hidden_dim, bias=False)
        self.k_proj = nn.Linear(config.hidden_dim, config.hidden_dim, bias=False)
        self.v_proj = nn.Linear(config.hidden_dim, config.hidden_dim, bias=False)

        # Output projection
        self.o_proj = nn.Linear(config.hidden_dim, config.hidden_dim, bias=False)

        self.dropout = nn.Dropout(config.dropout)

    def forward(
        self,
        x: torch.Tensor,
        rope_freqs: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        batch_size, seq_len, _ = x.shape

        # Project to Q, K, V
        q = self.q_proj(x).view(batch_size, seq_len, self.num_heads, self.head_dim)
        k = self.k_proj(x).view(batch_size, seq_len, self.num_heads, self.head_dim)
        v = self.v_proj(x).view(batch_size, seq_len, self.num_heads, self.head_dim)

        # Apply rotary position embeddings to Q and K
        q = apply_rope(q, rope_freqs[:seq_len])
        k = apply_rope(k, rope_freqs[:seq_len])

        # Transpose to (batch, heads, seq_len, head_dim) for attention
        q = q.transpose(1, 2)
        k = k.transpose(1, 2)
        v = v.transpose(1, 2)

        # Scaled dot-product attention with causal mask
        # Using PyTorch's built-in efficient attention when available
        attn_output = F.scaled_dot_product_attention(
            q, k, v,
            attn_mask=mask,
            is_causal=(mask is None),  # Use built-in causal mask if no custom mask
            dropout_p=self.dropout.p if self.training else 0.0,
        )

        # Reshape back: (batch, heads, seq_len, head_dim) → (batch, seq_len, hidden_dim)
        attn_output = attn_output.transpose(1, 2).contiguous().view(batch_size, seq_len, self.hidden_dim)

        # Output projection
        return self.o_proj(attn_output)


# ── SwiGLU Feed-Forward Network ───────────────────────────────────────────────

class SwiGLUFFN(nn.Module):
    """
    Feed-forward network with SwiGLU activation.

    SwiGLU = Swish(x · W_gate) ⊙ (x · W_up), then project down.
    More expressive than standard ReLU/GELU FFN, used in LLaMA/PaLM.

    Note: SwiGLU uses 3 weight matrices instead of 2, so intermediate_dim
    should be ~2/3 of what you'd use for a standard FFN to keep param count similar.
    """

    def __init__(self, config: ModelConfig):
        super().__init__()
        self.gate_proj = nn.Linear(config.hidden_dim, config.intermediate_dim, bias=False)
        self.up_proj = nn.Linear(config.hidden_dim, config.intermediate_dim, bias=False)
        self.down_proj = nn.Linear(config.intermediate_dim, config.hidden_dim, bias=False)
        self.dropout = nn.Dropout(config.dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # SwiGLU: swish(gate) * up, then down
        gate = F.silu(self.gate_proj(x))  # Swish = SiLU
        up = self.up_proj(x)
        return self.dropout(self.down_proj(gate * up))


# ── Transformer Block ─────────────────────────────────────────────────────────

class TransformerBlock(nn.Module):
    """
    Single transformer decoder block with pre-norm architecture.

    Structure:
        x → RMSNorm → Attention → + residual
        x → RMSNorm → SwiGLU FFN → + residual
    """

    def __init__(self, config: ModelConfig):
        super().__init__()
        self.attention_norm = RMSNorm(config.hidden_dim, eps=config.norm_eps)
        self.attention = CausalSelfAttention(config)
        self.ffn_norm = RMSNorm(config.hidden_dim, eps=config.norm_eps)
        self.ffn = SwiGLUFFN(config)

    def forward(
        self,
        x: torch.Tensor,
        rope_freqs: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        # Pre-norm attention with residual connection
        x = x + self.attention(self.attention_norm(x), rope_freqs, mask)
        # Pre-norm FFN with residual connection
        x = x + self.ffn(self.ffn_norm(x))
        return x


# ── Full Transformer Model ────────────────────────────────────────────────────

class PromptPolisherTransformer(nn.Module):
    """
    The complete Prompt Polisher Transformer decoder model.

    This is a causal (autoregressive) language model that takes tokenized
    prompts and generates optimized versions token by token.

    Architecture summary:
    - Token embeddings (no positional — RoPE handles positions)
    - N × TransformerBlock (RMSNorm → Attention → RMSNorm → SwiGLU)
    - Final RMSNorm
    - Linear head (tied with embeddings for parameter efficiency)
    """

    def __init__(self, config: ModelConfig):
        super().__init__()
        self.config = config

        # Token embedding (maps token IDs → vectors)
        self.token_embedding = nn.Embedding(config.vocab_size, config.hidden_dim)

        # Embedding dropout
        self.embed_dropout = nn.Dropout(config.dropout)

        # Transformer blocks
        self.layers = nn.ModuleList([
            TransformerBlock(config) for _ in range(config.num_layers)
        ])

        # Final normalization before output head
        self.final_norm = RMSNorm(config.hidden_dim, eps=config.norm_eps)

        # Output head — projects hidden states back to vocabulary logits
        # We tie weights with the token embedding for parameter efficiency
        self.output_head = nn.Linear(config.hidden_dim, config.vocab_size, bias=False)
        self.output_head.weight = self.token_embedding.weight  # Weight tying

        # Precompute RoPE frequencies (not a parameter, just a buffer)
        rope_freqs = precompute_rope_frequencies(config.head_dim, config.max_seq_len)
        self.register_buffer("rope_freqs", rope_freqs, persistent=False)

        # Initialize weights
        self._init_weights()

    def _init_weights(self):
        """Initialize model weights following GPT-2 / LLaMA conventions."""
        for module in self.modules():
            if isinstance(module, nn.Linear):
                torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
                if module.bias is not None:
                    torch.nn.init.zeros_(module.bias)
            elif isinstance(module, nn.Embedding):
                torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)

    def forward(
        self,
        input_ids: torch.Tensor,
        labels: Optional[torch.Tensor] = None,
        mask: Optional[torch.Tensor] = None,
    ) -> dict:
        """
        Forward pass.

        Args:
            input_ids: (batch_size, seq_len) — token IDs
            labels: (batch_size, seq_len) — target token IDs for loss computation
                    Typically input_ids shifted right by one position.
                    Use -100 for positions to ignore in loss.
            mask: Optional attention mask

        Returns:
            dict with keys:
                "logits": (batch_size, seq_len, vocab_size)
                "loss": scalar (only if labels provided)
        """
        batch_size, seq_len = input_ids.shape
        assert seq_len <= self.config.max_seq_len, \
            f"Sequence length {seq_len} exceeds max {self.config.max_seq_len}"

        # Token embeddings
        x = self.token_embedding(input_ids)
        x = self.embed_dropout(x)

        # Pass through transformer blocks
        for layer in self.layers:
            x = layer(x, self.rope_freqs, mask)

        # Final norm + output projection
        x = self.final_norm(x)
        logits = self.output_head(x)

        result = {"logits": logits}

        # Compute loss if labels provided
        if labels is not None:
            # Shift logits and labels for next-token prediction
            # logits[:, :-1] predicts labels[:, 1:]
            shift_logits = logits[:, :-1, :].contiguous()
            shift_labels = labels[:, 1:].contiguous()
            loss = F.cross_entropy(
                shift_logits.view(-1, self.config.vocab_size),
                shift_labels.view(-1),
                ignore_index=-100,  # Ignore padding tokens
            )
            result["loss"] = loss

        return result

    def count_parameters(self) -> int:
        """Count actual trainable parameters."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)

    @torch.no_grad()
    def generate(
        self,
        input_ids: torch.Tensor,
        max_new_tokens: int = 256,
        temperature: float = 0.8,
        top_k: int = 50,
        top_p: float = 0.9,
        eos_token_id: int = 3,
    ) -> torch.Tensor:
        """
        Autoregressive text generation with sampling.

        Args:
            input_ids: (batch_size, prompt_len) — tokenized prompt
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature (lower = more deterministic)
            top_k: Keep only top-k logits before sampling
            top_p: Nucleus sampling threshold
            eos_token_id: Stop generation when this token is produced

        Returns:
            (batch_size, prompt_len + generated_len) — full sequence with generated tokens
        """
        self.eval()

        for _ in range(max_new_tokens):
            # Crop to max context length if needed
            idx_cond = input_ids if input_ids.size(1) <= self.config.max_seq_len \
                else input_ids[:, -self.config.max_seq_len:]

            # Forward pass
            output = self.forward(idx_cond)
            logits = output["logits"][:, -1, :]  # Only last position

            # Apply temperature
            if temperature > 0:
                logits = logits / temperature

                # Top-k filtering
                if top_k > 0:
                    top_k_values, _ = torch.topk(logits, min(top_k, logits.size(-1)))
                    logits[logits < top_k_values[:, -1:]] = float("-inf")

                # Top-p (nucleus) filtering
                if top_p < 1.0:
                    sorted_logits, sorted_indices = torch.sort(logits, descending=True)
                    cumulative_probs = torch.cumsum(F.softmax(sorted_logits, dim=-1), dim=-1)
                    # Remove tokens with cumulative probability above threshold
                    sorted_mask = cumulative_probs - F.softmax(sorted_logits, dim=-1) >= top_p
                    sorted_logits[sorted_mask] = float("-inf")
                    # Scatter back
                    logits = sorted_logits.scatter(1, sorted_indices, sorted_logits)

                # Sample from distribution
                probs = F.softmax(logits, dim=-1)
                next_token = torch.multinomial(probs, num_samples=1)
            else:
                # Greedy decoding (temperature = 0)
                next_token = logits.argmax(dim=-1, keepdim=True)

            # Append generated token
            input_ids = torch.cat([input_ids, next_token], dim=1)

            # Stop if EOS token generated (for all sequences in batch)
            if (next_token == eos_token_id).all():
                break

        return input_ids


# ── Factory Function ──────────────────────────────────────────────────────────

def create_model(config: Optional[ModelConfig] = None) -> PromptPolisherTransformer:
    """Create a model instance from config. Uses base config if none provided."""
    if config is None:
        from ai.src.training.config import get_base_config
        config = get_base_config()

    model = PromptPolisherTransformer(config)
    param_count = model.count_parameters()
    print(f"🧠 Created PromptPolisherTransformer")
    print(f"   Layers: {config.num_layers} | Hidden: {config.hidden_dim} | Heads: {config.num_heads}")
    print(f"   Parameters: {param_count:,} ({param_count/1e6:.1f}M)")
    return model


if __name__ == "__main__":
    # Quick smoke test
    from ai.src.training.config import get_base_config

    config = get_base_config()
    model = create_model(config)

    # Test forward pass
    dummy_input = torch.randint(0, config.vocab_size, (2, 64))
    output = model(dummy_input, labels=dummy_input)
    print(f"\n✅ Forward pass OK")
    print(f"   Input shape:  {dummy_input.shape}")
    print(f"   Logits shape: {output['logits'].shape}")
    print(f"   Loss: {output['loss'].item():.4f}")

    # Test generation
    prompt = torch.randint(0, config.vocab_size, (1, 10))
    generated = model.generate(prompt, max_new_tokens=20)
    print(f"\n✅ Generation OK")
    print(f"   Prompt length: 10")
    print(f"   Generated length: {generated.shape[1]}")
