# Small Models Hack — Starter Kit

Hackathon starter code for SundAI's "Small Models Hack." Each track is a self-contained directory you can push to GitHub as its own repo.

## Tracks

| Repo | Theme | What you build |
|---|---|---|
| [smallbench](./smallbench) | Benchmarking & Evals | A reproducible eval harness comparing local models on real tasks |
| [pocketcoder](./pocketcoder) | Harnesses & Infra | A local Claude-Code-style coding agent that runs entirely offline |
| [airgap](./airgap) | Local-First Apps | Private RAG over your own docs, on-device only |
| [shrinkray](./shrinkray) | Pushing the Limits | Quantization comparisons, model routing, and a distillation scaffold |

Each track has its own `README.md` with a step-by-step guide and a "Suggested Challenges" section to extend the starter into a hackathon submission.

## Common prerequisites

- Python 3.10+
- [Ollama](https://ollama.com) installed (`curl -fsSL https://ollama.com/install.sh | sh`)
- 16GB+ RAM (24GB+ recommended for 12B models)

All four tracks default to **Google Gemma 4** as the local model and talk to it over Ollama's OpenAI-compatible API at `http://localhost:11434/v1`. Swap in llama.cpp, vLLM, LM Studio, or MLX by pointing `OPENAI_BASE_URL` elsewhere — every example uses the same `client.py` pattern.

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
