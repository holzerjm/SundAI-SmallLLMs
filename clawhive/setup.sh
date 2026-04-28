#!/usr/bin/env bash
set -euo pipefail

if ! command -v ollama >/dev/null; then
  echo "ollama not found. install from https://ollama.com first."
  exit 1
fi

python3 -m pip install --quiet openai anthropic rich

# local models — both sizes used by the swarm
ollama pull gemma4:4b
ollama pull gemma4:1b

# optional: gemma4:12b for the CLAWHIVE_PLANNER_LOCAL fallback
# (skip this if you have a frontier API key)
ollama pull gemma4:12b || true

echo
echo "ZeroClaw is optional — only needed for the chat surface integration."
echo "Install it with: cargo install zeroclaw  (requires Rust)"
echo "Or download a prebuilt binary from https://github.com/zeroclaw-labs/zeroclaw/releases"
echo
echo "ready. try:"
echo "  python orchestrator.py 'Build a Python script that prints the top 10 HN stories as markdown.'"
echo "  python cli.py     # interactive REPL"
echo "  python examples/coding_task.py"
echo
echo "frontier planning needs an API key:"
echo "  export ANTHROPIC_API_KEY=sk-ant-..."
echo "  export OPENAI_API_KEY=sk-..."
echo "  # or for no-API-key fallback:"
echo "  export CLAWHIVE_PLANNER_LOCAL=1"
