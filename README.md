# Transformer from Scratch — NumPy → PyTorch → a Trained Language Model

A decoder-only transformer language model built from first principles. Every core component is implemented twice — first in pure NumPy to establish the mathematics, then in PyTorch — and the PyTorch components are assembled into a full character-level language model trained on a corpus of classic literature and philosophy.

The implementation deliberately avoids `nn.Transformer`. Scaled dot-product attention, multi-head splitting, sinusoidal positional encoding, layer normalization, the feed-forward network, the causal mask, the training loop, and autoregressive sampling are all written out explicitly.

```
prompt: "War never"

War never held and tragedy on the rage of his audacemy. He went on a sent
circumstom and hisson, for all within them. Therefore wonderful of heaten
heart. And he made agains him to her heart hand. He could have him to see as
maintaining was almost temper to him...
```

*An actual sample from the trained model. Working one character at a time with no dictionary, it learned to spell, punctuate, and form grammatically plausible English — invented words like "audacemy" are the signature of a character-level model.*

## Table of Contents

- [Motivation](#motivation)
- [Repository Structure](#repository-structure)
- [Architecture](#architecture)
- [Training](#training)
- [Usage](#usage)
- [Engineering Notes](#engineering-notes)
- [Roadmap](#roadmap)
- [Tech Stack](#tech-stack)

## Motivation

The goal was to understand the transformer at the level of its primitives rather than as a library abstraction. Implementing each component in NumPy first forces the matrix shapes and the underlying mathematics to be correct with no framework to fall back on; re-implementing in PyTorch then maps those same ideas onto autograd, `nn.Module`, and GPU execution. The result is a working language model and, more importantly, a complete mental model of how each part contributes to the whole.

## Repository Structure

The project is organized as a two-pass progression. Each component exists in a from-scratch NumPy form (`numpy_from_scratch/`) and a PyTorch form (`pytorch_components/`); the full trainable model lives at the repository root.

| Component | NumPy — `numpy_from_scratch/` | PyTorch — `pytorch_components/` |
|---|---|---|
| Softmax | `Softmax.py` | — |
| Scaled dot-product attention | `single_head_attention.py` | — |
| Multi-head attention | `multi_head_attention.ipynb` | `multi_head_attention_in_pytorch.ipynb` |
| Positional encoding | `positional_encoding.ipynb` | `positional_encoding_in_pytorch.ipynb` |
| Feed-forward network | `feed_forward.ipynb` | `feed_forward_in_pytorch.ipynb` |
| Layer normalization | `layer_norm.ipynb` | `layer_norm_in_pytorch.ipynb` |
| Transformer block | `transformer_block.ipynb` | `transformer_block_in_pytorch.ipynb` |
| **Full trainable model** | — | **`full_model_transformer_in_pytorch.ipynb`** (root) |

The capstone is [`full_model_transformer_in_pytorch.ipynb`](full_model_transformer_in_pytorch.ipynb), which wires the components together, builds a character-level tokenizer, trains the model, and generates text.

## Architecture

```
token ids
   │
   ▼
Embedding ──► + Sinusoidal Positional Encoding
   │
   ▼
N × Transformer Block
   │   ├─ Multi-Head Self-Attention (causal mask)  ─► residual ─► LayerNorm
   │   └─ Feed-Forward (d → 4d → d, ReLU)           ─► residual ─► LayerNorm
   ▼
Linear (d_model → vocab_size)
   │
   ▼
logits over the vocabulary
```

Notable implementation details:

- **Multi-head attention** — Q/K/V are bias-free linear projections (`bias=False`), reshaped into heads and computed as a single batched matmul rather than a Python loop over heads. The causal mask (`triu`, diagonal 1) is precomputed in `__init__` as a registered buffer; the per-head dimension is computed once at init. Neither is rebuilt on the forward pass.
- **Positional encoding** — sinusoidal, fully vectorized with `torch.arange` and broadcasting, precomputed into a buffer at initialization.
- **Layer normalization** — implemented by hand with learnable `gamma` and `beta` parameters rather than `nn.LayerNorm`.
- **Normalization placement** — post-norm (residual, then normalize).
- **Tokenizer** — character level; the vocabulary is derived from the sorted set of characters present in the corpus.

## Training

Configuration from the committed run:

| Hyperparameter | Value |
|---|---|
| `d_model` | 256 |
| `num_heads` | 4 |
| `num_blocks` | 6 |
| `block_size` (context) | 128 |
| `batch_size` | 64 |
| Optimizer | AdamW, `lr = 3e-4` |
| Loss | Cross-entropy (next-token) |
| Steps | 5,000 |

5,611,698 parameters (≈5.6M), trained on a GTX 1650 (4 GB VRAM). Training loss reached ~1.3 at step 5,000.

The training corpus consists of public-domain classic literature and philosophy (Tolstoy, Sun Tzu, Aristotle, Aquinas, Augustine, Balzac, and others). The `data/` directory is gitignored; supply your own `.txt` files there to train.

Generation is autoregressive with top-k sampling (k = 10): the final-position logits are passed through softmax, all but the top 10 candidates are masked to zero, and the next token is drawn with `multinomial`, advancing the context window one token at a time.

## Usage

```bash
pip install torch
# place one or more .txt files in ./data
jupyter notebook full_model_transformer_in_pytorch.ipynb
```

Run the cells top to bottom: build the vocabulary, batch the data, train, and generate.

## Engineering Notes

Several bugs encountered during development are preserved in the notebooks, along with their resolutions:

- **Missing causal mask** — without it the model attended to future tokens during training and failed at generation. Resolved with an upper-triangular mask and `masked_fill(-inf)` before softmax. Training and inference must condition on the same information.
- **Positional encoding exponent** — because the loop index already advances in steps of 2, an extra `2*i` factor double-counted the exponent; using the index directly (`i/d_model`) restores the correct sinusoidal frequencies.
- **Dimension mismatch** — training fed `(batch, seq_len)` while generation fed `(seq_len,)`; resolved with `unsqueeze(0)`.
- **Tensor wrapping** — re-wrapping a `multinomial` result in `torch.tensor([...])` produced an incompatible shape for `torch.cat`.

## Roadmap

- **BPE tokenization** — replace character-level tokens with subwords for longer semantic context.
- **Experiment tracking** — self-hosted MLflow to log runs and compare configurations (character vs. BPE, baseline vs. scaled).
- **Scale-up** — `d_model=384`, 8 blocks, context 256, with mixed precision, gradient accumulation, gradient clipping, gradient checkpointing, and an LR warmup + cosine schedule to fit the larger model within 4 GB.
- **Architecture upgrades** — pre-norm, RMSNorm, dropout, weight tying, and eventually RoPE and grouped-query attention.

## Tech Stack

Python · NumPy · PyTorch · Jupyter
