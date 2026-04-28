#!/usr/bin/env bash
set -euo pipefail

if ! command -v ollama >/dev/null; then
  echo "ollama not found. install from https://ollama.com first."
  exit 1
fi

python3 -m pip install --quiet openai

ollama pull qwen3:8b

echo
echo "ready. try:"
echo "  python agent.py 'list files in this directory and summarize the project'"
echo "  python cli.py    # for interactive mode"
