#!/usr/bin/env bash
set -euo pipefail

if ! command -v ollama >/dev/null; then
  echo "ollama not found. install from https://ollama.com first."
  exit 1
fi

python3 -m pip install --quiet openai

# small + medium for routing
ollama pull qwen3:1.7b
ollama pull qwen3:8b

# different quants of the same model for the comparison
# (Ollama serves quantized variants by tag; check `ollama search qwen3` for what's available)
ollama pull qwen3:8b-q4_K_M || true
ollama pull qwen3:8b-q8_0   || true

echo
echo "ready. try:"
echo "  python quant_compare.py"
echo "  python router.py 'What is the average order value by customer in 2024?'"
echo "  python distill.py generate --n 50 --out training.jsonl"
