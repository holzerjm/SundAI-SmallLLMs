# Small Models Hack — Starter Kit

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Made with Python](https://img.shields.io/badge/made%20with-Python-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![Ollama](https://img.shields.io/badge/Ollama-local%20LLM-000000?logo=ollama&logoColor=white)](https://ollama.com)
[![Hackathon](https://img.shields.io/badge/event-hackathon-orange.svg)](#)

Hackathon starter code for SundAI's "Small Models Hack." Each track is a self-contained directory you can work in independently.

## Tracks

### Starter tracks

| Repo | Theme | What you build |
|---|---|---|
| [smallbench](./smallbench) | Benchmarking & Evals | A reproducible eval harness comparing local models on real tasks |
| [pocketcoder](./pocketcoder) | Harnesses & Infra | A local Claude-Code-style coding agent that runs entirely offline |
| [airgap](./airgap) | Local-First Apps | Private RAG over your own docs (dense embeddings), on-device only |
| [shrinkray](./shrinkray) | Pushing the Limits | Quantization comparisons, model routing, and a distillation scaffold |

### Advanced tracks

| Repo | Theme | What you build |
|---|---|---|
| [clawhive](./clawhive) | Multi-Agent Orchestration | A Plan → Act → Critique swarm using [ZeroClaw](https://github.com/zeroclaw-labs/zeroclaw) as the chat surface; mixes frontier Claude with local Gemma 4 workers |
| [nanochat](./nanochat) | Streaming Q&A over a corpus | A Streamlit chat app with lexical retrieval (no embeddings), inspired by the [DataCamp Nemotron-3 Nano tutorial](https://www.datacamp.com/tutorial/nemotron-3-nano-tutorial); local Gemma 4 by default, one-flag swap to Nemotron-3 Nano via Ollama Cloud |

The starter tracks are scoped for a weekend with one or two builders. The advanced tracks assume you've already shipped something local-LLM-shaped before, or you're a team of three+ who want to coordinate on a deeper system.

Each track has its own `README.md` with a step-by-step guide and a "Suggested Challenges" section to extend the starter into a hackathon submission.

## Common prerequisites

- Python 3.10+
- [Ollama](https://ollama.com) installed (`curl -fsSL https://ollama.com/install.sh | sh`)
- 16GB+ RAM (24GB+ recommended for 12B models)
- Optional: an Anthropic or OpenAI API key (only the `clawhive` track needs frontier access; everything else is fully local)

All tracks default to **Google Gemma 4** as the local model and talk to it over Ollama's OpenAI-compatible API at `http://localhost:11434/v1`. Swap in llama.cpp, vLLM, LM Studio, or MLX by pointing `OPENAI_BASE_URL` elsewhere — every example uses the same `client.py` pattern.

To use a different model family (Qwen, Llama, Mistral, Phi), set the per-track env var (e.g., `POCKETCODER_MODEL=qwen3:8b`) or edit the track's `client.py`.

## Hardware tiers (Gemma 4)

| RAM | Suggested model |
|---|---|
| 8GB | `gemma4:1b` |
| 16GB | `gemma4:4b` (default in all tracks) |
| 24GB+ | `gemma4:12b` |
| 64GB+ | `gemma4:27b` |

## Pick your track

```bash
cd smallbench && ./setup.sh && cat README.md
```

## How the tracks fit together

If you want to combine tracks for an ambitious submission:

- **smallbench + any other track** — Use smallbench as the eval harness for whatever you build. Every other track produces something measurable.
- **shrinkray + clawhive** — Distill a specialized small model in shrinkray, then plug it into clawhive as one of the workers. Demo a swarm where one agent is a fine-tune of yours.
- **airgap + nanochat** — Build the same Q&A workload twice: once with dense retrieval (airgap), once with lexical (nanochat). Find the corpus regime where each wins.
- **pocketcoder + clawhive** — Use pocketcoder's tool-calling harness as the "coder" role inside clawhive's swarm. Now the coder can edit files and run tests, not just emit code.
