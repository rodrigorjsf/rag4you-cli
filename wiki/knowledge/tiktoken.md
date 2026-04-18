# tiktoken — Token Counting Library

**Summary**: tiktoken is OpenAI's fast BPE tokenizer library for Python (written in Rust). It provides token counting for OpenAI models. The rag4you-cli project uses it for token economy metrics in SP0 benchmarks and for chunk size calculations.
**Sources**: `docs/references/toolchain/bibliography.md`, https://github.com/openai/tiktoken, https://pypi.org/project/tiktoken/, https://cookbook.openai.com/examples/how_to_count_tokens_with_tiktoken
**Last updated**: 2025-07-22
---

## Installation

```bash
uv add tiktoken
```

## Core API

### Get encoding by name

```python
import tiktoken

enc = tiktoken.get_encoding("cl100k_base")
tokens = enc.encode("hello world")
print(len(tokens))  # Token count
print(enc.decode(tokens))  # "hello world"
```

### Get encoding for a model

```python
enc = tiktoken.encoding_for_model("gpt-4")
enc = tiktoken.encoding_for_model("gpt-4o")
```

### Available encodings

| Encoding | Models |
|---|---|
| `o200k_base` | GPT-4o, GPT-4o-mini |
| `cl100k_base` | GPT-4, GPT-3.5-turbo, text-embedding-ada-002, text-embedding-3-small/large |
| `p50k_base` | Codex models |
| `r50k_base` / `gpt2` | GPT-3 |

## Token counting patterns

### Basic counting

```python
import tiktoken

def count_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
    """Count tokens in a text string."""
    enc = tiktoken.get_encoding(encoding_name)
    return len(enc.encode(text))
```

### Batch counting

```python
def count_tokens_batch(texts: list[str], encoding_name: str = "cl100k_base") -> list[int]:
    """Count tokens for multiple texts."""
    enc = tiktoken.get_encoding(encoding_name)
    return [len(enc.encode(text)) for text in texts]
```

### Token economy metrics

For benchmarking RAG systems (SP0, see [[ir-evaluation-benchmarking]]):

```python
import tiktoken

def compute_token_metrics(
    query: str,
    retrieved_chunks: list[str],
    response: str,
    encoding_name: str = "cl100k_base",
) -> dict[str, int]:
    """Compute token economy metrics for a RAG query."""
    enc = tiktoken.get_encoding(encoding_name)
    return {
        "query_tokens": len(enc.encode(query)),
        "context_tokens": sum(len(enc.encode(c)) for c in retrieved_chunks),
        "response_tokens": len(enc.encode(response)),
        "total_tokens": (
            len(enc.encode(query))
            + sum(len(enc.encode(c)) for c in retrieved_chunks)
            + len(enc.encode(response))
        ),
        "num_chunks": len(retrieved_chunks),
    }
```

### Chunk size validation

```python
def validate_chunk_size(text: str, max_tokens: int = 512) -> bool:
    """Check if text fits within token budget."""
    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text)) <= max_tokens

def split_by_tokens(text: str, max_tokens: int = 512) -> list[str]:
    """Split text into token-bounded chunks (naive split)."""
    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(text)
    chunks = []
    for i in range(0, len(tokens), max_tokens):
        chunk_tokens = tokens[i:i + max_tokens]
        chunks.append(enc.decode(chunk_tokens))
    return chunks
```

## Performance

tiktoken is 3-6x faster than comparable tokenizers (like HuggingFace's `tokenizers` library) because its core is written in Rust.

## What is BPE

Byte Pair Encoding (BPE) converts text to tokens:
- **Reversible and lossless** — tokens decode back to original text
- **Works on arbitrary text** — handles any input
- **Compresses text** — average ~4 bytes per token
- **Subword-aware** — common subwords like "ing" become single tokens

## Educational API

```python
from tiktoken._educational import *

# Visualize how GPT-4 encoder works
enc = SimpleBytePairEncoding.from_tiktoken("cl100k_base")
enc.encode("hello world aaaaaaaaaaaa")
```

## Relevance to rag4you-cli

- **SP0 (bench/)**: Token economy metrics (query tokens, context tokens, response tokens)
- **SP1 (rag4you/)**: Chunk size validation and token-based splitting (see [[rag-research-compendium]])
- **Encoding choice**: Use `cl100k_base` as the default (covers GPT-4, GPT-3.5, embeddings)
- **Configuration**: Encoding name should be configurable (not hardcoded) per project convention

## Related pages

- [[ir-evaluation-benchmarking]]
- [[rag-research-compendium]]
- [[mcp-protocol]]
- [[pydantic-v2]]
- [[python-uv]]
