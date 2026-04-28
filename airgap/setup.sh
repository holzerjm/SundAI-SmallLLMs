#!/usr/bin/env bash
set -euo pipefail

if ! command -v ollama >/dev/null; then
  echo "ollama not found. install from https://ollama.com first."
  exit 1
fi

python3 -m pip install --quiet openai numpy gradio

ollama pull gemma4:4b
ollama pull nomic-embed-text

echo
echo "ready. try:"
echo "  python ingest.py ./sample_docs --out index.json"
echo "  python rag.py --index index.json 'what is in these docs?'"
echo "  python app.py --index index.json"
