# airgap

Private RAG over your own documents. Everything runs on-device — no embeddings, queries, or document content leaves your machine.

Built for the SundAI Small Models Hack as a starting point for "private/sensitive domain" applications: legal docs, medical notes, financial records, personal journals, internal company wikis.

## What's in here

```
airgap/
├── client.py          # local chat + embedding clients (both via Ollama)
├── ingest.py          # walk a directory, chunk, embed, save index
├── rag.py             # retrieve top-k chunks, ask a question
├── app.py             # gradio UI
└── sample_docs/       # tiny example corpus
```

## Step-by-step

### 1. Setup

```bash
./setup.sh
```

Pulls `qwen3:8b` (chat), `nomic-embed-text` (embeddings), and installs `numpy` and `gradio`.

### 2. Ingest a folder

```bash
python ingest.py ./sample_docs --out index.json
```

This walks the directory, chunks every `.md`, `.txt`, `.py`, `.rst` file, embeds each chunk, and writes a single `index.json` (chunks + vectors).

For your own docs:

```bash
python ingest.py ~/Documents/notes --out my-index.json
```

### 3. Ask a question from the CLI

```bash
python rag.py --index index.json "what does this codebase do?"
```

You'll see the top-k chunks the system retrieved, then the model's grounded answer.

### 4. Launch the UI

```bash
python app.py --index index.json
```

Opens a Gradio chat at `http://localhost:7860`. Ask questions, see source chunks.

### 5. Check that it's actually airgapped

While the app is running:

```bash
# in another terminal — block all outbound network
sudo pfctl -e   # or use Little Snitch / Lulu
```

The app should still answer questions. If it stops, you have a leak somewhere — debug it.

Or just use [Little Snitch](https://www.obdev.at/products/littlesnitch/) and watch the network tab while you query.

## Suggested challenges

1. **Private Sensitive-Domain Assistant** — Pick a real workflow (redact a contract, summarize a medical chart, classify expenses) and ship it. Demo with the network off.
2. **Personal Knowledge Worker** — Ingest your `~/Documents`, Apple Notes export, and Obsidian vault. Build a chat that knows your life.
3. **Hybrid Retrieval** — Add BM25 alongside dense retrieval. Compare recall on a labeled question set.
4. **Long-context vs. RAG** — Some local models claim 1M context. Test: at what corpus size does RAG beat shoving everything in the prompt?
5. **Citations & Provenance** — Make the model emit citations like `[doc.md:42]` and verify them. Refuse to answer when retrieval confidence is low.
6. **Mobile/Edge Demo** — Get the same RAG running on an iPhone via [MLX-Swift](https://github.com/ml-explore/mlx-swift) or on a Raspberry Pi.

## Why this is a good hackathon project

- The setup is simple enough to do in 15 minutes.
- "Private" is a real product wedge — there are actual users who can't put their data in OpenAI's API.
- The "demo with the wifi off" moment is genuinely impressive to a non-technical audience.
- Most of the interesting work (chunking, retrieval, prompt design) is small-model-specific.

## Notes on the approach

- **Embeddings**: `nomic-embed-text` (137M params, 768-dim). Small, fast, runs locally via Ollama.
- **Storage**: JSON file with numpy-loaded vectors. Fine for <50k chunks. For more, swap in [LanceDB](https://lancedb.com) or sqlite-vss.
- **Chunking**: Naive 1000-char overlap chunks. Beat this with smarter strategies.
- **Retrieval**: Cosine similarity, top-5. No reranking (yet).
