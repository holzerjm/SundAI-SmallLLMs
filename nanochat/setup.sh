#!/usr/bin/env bash
set -euo pipefail

if ! command -v ollama >/dev/null; then
  echo "ollama not found. install from https://ollama.com first."
  exit 1
fi

python3 -m pip install --quiet ollama streamlit

ollama pull gemma4:4b

mkdir -p sample_corpus
echo
echo "ready. try:"
echo "  python corpus.py ./sample_corpus --out corpus.json"
echo "  python chat.py --corpus corpus.json 'what is in these docs?'"
echo "  streamlit run app.py -- --corpus corpus.json"
echo
echo "to enable Nemotron-3 Nano via Ollama Cloud:"
echo "  export OLLAMA_API_KEY=..."
echo "  export NANOCHAT_USE_NEMOTRON=1"
