#!/usr/bin/env bash
set -euo pipefail

if ! command -v ollama >/dev/null; then
  echo "ollama not found. install from https://ollama.com first."
  exit 1
fi

python3 -m pip install --quiet openai rich

echo "pulling models (this is the slow part)..."
ollama pull qwen3:8b
ollama pull gemma3:4b

mkdir -p results
echo
echo "ready. try:  python bench.py --model qwen3:8b --out results/qwen3-8b.json"
