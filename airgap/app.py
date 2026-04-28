"""Gradio chat UI on top of rag.py."""
import argparse

import gradio as gr

from client import make_client
from rag import load_index, answer


def build_app(index_path: str):
    client = make_client()
    index = load_index(index_path)
    print(f"loaded {len(index['records'])} chunks from {index_path}")

    def respond(message: str, history: list):
        out, hits = answer(client, index, message, k=5)
        sources = "\n".join(f"- `{h['path']}:{h['chunk_id']}` (score={h['score']:.3f})" for h in hits)
        return f"{out}\n\n---\n**sources:**\n{sources}"

    return gr.ChatInterface(
        respond,
        type="messages",
        title="airgap — private RAG",
        description=f"Querying {len(index['records'])} chunks. Everything runs locally.",
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", default="index.json")
    ap.add_argument("--port", type=int, default=7860)
    args = ap.parse_args()
    build_app(args.index).launch(server_port=args.port)


if __name__ == "__main__":
    main()
