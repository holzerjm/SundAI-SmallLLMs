#!/usr/bin/env bash
set -euo pipefail

if ! command -v ollama >/dev/null; then
  echo "ollama not found. install from https://ollama.com first."
  exit 1
fi

python3 -m pip install --quiet openai rich

echo "pulling models (this is the slow part)..."
ollama pull gemma4:4b
ollama pull gemma4:1b

mkdir -p results
echo
echo "ready. try:  python bench.py --model gemma4:4b --out results/gemma4-4b.json"
