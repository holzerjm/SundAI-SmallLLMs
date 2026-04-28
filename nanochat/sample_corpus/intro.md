# nanochat — Sample Corpus

This is a tiny example corpus you can use to test the nanochat pipeline before pointing it at your own documents. Try queries like:

- "what is nanochat?"
- "what's the difference between smart and all mode?"
- "what model does nanochat default to?"
- "what is something not in this corpus?"  (should refuse)

## What nanochat is

nanochat is a streaming chat / Q&A interface over a corpus of documents. It is part of the SundAI Small Models Hack starter kit. It demonstrates lexical retrieval (no embeddings, no vector database) over a JSON-based corpus artifact.

## Retrieval modes

nanochat supports two retrieval modes:

- **smart**: Score each segment by keyword overlap with the query, then pack the top-scoring segments into the model's context up to a token budget. This works well for focused questions over large corpora.
- **all**: Pack as much of the corpus as fits, in document order, with no scoring. This works when the corpus is small enough to fit in the context window of a long-context model.

The smart scorer is a simplified TF-IDF. A real BM25 implementation would be a worthwhile improvement and is one of the suggested challenges in the README.

## Default model

nanochat defaults to Google Gemma 4 (`gemma4:4b`) running locally via Ollama. You can swap to NVIDIA Nemotron-3 Nano (a 30B mixture-of-experts model) via Ollama Cloud by setting `NANOCHAT_USE_NEMOTRON=1` and `OLLAMA_API_KEY`.

## When you would use this approach

- You have a corpus that fits in the context window of a long-context model, or close to it.
- You don't want to maintain a vector database, embedding pipeline, or re-indexing process.
- Your queries tend to share vocabulary with the corpus (which is most of the time, in practice).
- You need on-device retrieval where running an embedding model is expensive.

## When you would NOT use this approach

- The corpus is much larger than any feasible context window.
- Queries and documents use very different vocabulary (the embeddings approach in airgap is better here).
- You need cross-lingual retrieval.
- You need hybrid retrieval over structured + unstructured data.
