# nanochat

**Advanced track.** A streaming chat / Q&A interface over a corpus of documents, built on the pattern from DataCamp's [Nemotron-3 Nano tutorial](https://www.datacamp.com/tutorial/nemotron-3-nano-tutorial). Defaults to local Gemma 4; one env var swaps in NVIDIA Nemotron-3 Nano (30B MoE) via Ollama Cloud for a side-by-side comparison.

## Why this is interesting

The [airgap](../airgap) track does dense-vector RAG. nanochat does the *other thing*: **lexical retrieval with no embeddings**. The Nemotron tutorial showed that for many corpora, smart keyword scoring + a long-context model beats vector search at a fraction of the engineering complexity.

That makes the interesting question for this track: **at what corpus size and query type does each approach win?** Build it, measure it, ship a writeup.

## What's in here

```
nanochat/
├── client.py            # local Ollama + Ollama Cloud (for Nemotron) under one API
├── corpus.py            # ingest a directory of text/markdown — no embeddings, just tokens
├── retrieval.py         # "smart" lexical scoring + "all" mode (truncate to context window)
├── chat.py              # streaming chat with corpus context + bounded history
├── app.py               # Streamlit UI (the demo surface)
├── compare.py           # head-to-head: local Gemma 4 vs Nemotron-3 Nano on a Q&A eval
└── sample_corpus/       # tiny example corpus to start
```

## Step-by-step

### 1. Setup

```bash
./setup.sh
```

Pulls `gemma4:4b` and installs Streamlit. Nemotron is opt-in (next step).

### 2. (Optional) enable Nemotron-3 Nano via Ollama Cloud

For the side-by-side comparison, sign up for [Ollama Cloud](https://ollama.com/cloud) and grab an API key:

```bash
export OLLAMA_API_KEY=...
export NANOCHAT_USE_NEMOTRON=1
```

When `NANOCHAT_USE_NEMOTRON=1`, the client routes to `nemotron-3-nano:30b-cloud` via the Ollama Cloud endpoint. Otherwise it stays fully local on Gemma 4.

### 3. Ingest a corpus

```bash
python corpus.py ./sample_corpus --out corpus.json
```

This walks the directory, tokenizes each file, and writes a single JSON artifact. **No embeddings, no vector DB, no GPU required for ingestion.** A 100MB corpus takes a few seconds.

For your own docs:

```bash
python corpus.py ~/Documents/notes --out my-corpus.json
```

### 4. Ask a question from the CLI

```bash
python chat.py --corpus corpus.json "what does this codebase do?"
```

You'll see which corpus segments scored highest, then the streamed answer.

### 5. Launch the Streamlit UI

```bash
streamlit run app.py -- --corpus corpus.json
```

```
┌─────────────────────────────────────────┐
│ nanochat — corpus-grounded Q&A          │
│ model: gemma4:4b   |   mode: smart      │
├─────────────────────────────────────────┤
│ user>  what does this code do?          │
│                                         │
│ assistant> [streaming]                  │
│   The corpus describes a hackathon...   │
│                                         │
│ sources: README.md (score 4.2),         │
│          intro.md (score 2.1)           │
└─────────────────────────────────────────┘
```

### 6. Compare local Gemma 4 vs Nemotron-3 Nano

```bash
python compare.py --corpus corpus.json --questions questions.txt
```

Runs the same questions against both models. Reports answer agreement, latency, and (if Nemotron is enabled) the cost gap. This is your hackathon submission's central chart.

## Suggested challenges

1. **Lexical vs Dense Bake-Off** — Run the same Q&A eval through nanochat (lexical) and airgap (dense). Find the corpus types where each wins. Plot recall@k.
2. **The Long-Context Crossover** — At what corpus size does "stuff everything in the prompt" beat retrieval? Sweep context window sizes 8k → 128k → 1M and find your model's crossover point.
3. **Multi-Document Reasoning** — Add questions that require synthesizing across documents. Does lexical retrieval find them? Does dense? Build a "multi-hop" eval.
4. **Citation Faithfulness** — Make the model emit `[doc.md:line]` citations and verify them. Refuse to answer if retrieval confidence is below a threshold.
5. **Adaptive Mode Switching** — Let the system pick "smart" (keyword retrieval) vs "all" (full context) per query, based on corpus size and query type. Measure quality + latency.
6. **Mobile/Offline** — Run nanochat on a phone (MLX-Swift) or a Raspberry Pi. The lexical retrieval path is way more feasible on weak hardware than the dense path.
7. **Beyond Keywords** — Replace the naive lexical scorer with BM25. Then add a tiny re-ranker (a small encoder model) on top. Measure each step's contribution.

## How this differs from the tutorial

The DataCamp tutorial shows the pattern. nanochat takes that pattern and:

- Defaults to **local Gemma 4** instead of Nemotron Cloud — so attendees can develop offline.
- Keeps Nemotron-3 Nano as a **one-env-var swap** for the comparison demo.
- Adds `compare.py` so you can produce real numbers, not just a UI screenshot.
- Drops the corpus into a single JSON artifact you can ship — no Streamlit session-state coupling for the data layer.

## Why "no embeddings"?

Embeddings are great. Vector DBs are great. But they introduce real complexity: a separate model, a separate storage layer, hyperparameters (chunk size, overlap, k, similarity threshold), and updates that require re-indexing.

For a corpus that fits in the context window of a long-context model, *concatenation* beats *retrieval*. For a corpus that's a bit too large, smart keyword scoring picks the relevant slice in milliseconds with no hyperparameters to tune.

The Nemotron tutorial's claim — and the question this track invites you to actually measure — is that this combination is "enough" for a surprisingly large class of real Q&A workloads.
