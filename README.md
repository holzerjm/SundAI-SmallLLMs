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
- 16GB+ RAM (32GB+ recommended for 30B models)

All four tracks talk to local models over Ollama's OpenAI-compatible API at `http://localhost:11434/v1`. Swap in llama.cpp, vLLM, LM Studio, or MLX by pointing `OPENAI_BASE_URL` elsewhere — every example uses the same `client.py` pattern.

## Hardware tiers

| RAM | Suggested models |
|---|---|
| 8GB | `qwen3:1.7b`, `gemma3:1b` |
| 16GB | `qwen3:8b`, `gemma3:4b`, `llama3.3:8b` |
| 24GB+ | `qwen3:14b`, `gemma3:12b` |
| 64GB+ | `qwen3:32b`, anything you want |

## Pick your track

```bash
cd smallbench && ./setup.sh && cat README.md
```
