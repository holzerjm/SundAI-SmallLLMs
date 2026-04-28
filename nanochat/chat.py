"""CLI entry point for nanochat. Streams the answer to stdout.

Usage:
  python chat.py --corpus corpus.json "what is X?"
  python chat.py --corpus corpus.json --mode all "summarize the docs"
"""
import argparse
import sys

from client import make_client, stream_chat
from retrieval import load, smart_retrieve, all_truncate, format_context


SYSTEM_MSG = (
    "You answer questions using ONLY the provided corpus context. Each context segment is "
    "preceded by a citation tag like [path:segment_id].\n\n"
    "Rules:\n"
    "- Cite the source after every factual claim using the bracket tag.\n"
    "- If the answer is not in the corpus, say: \"I don't know from the provided documents.\"\n"
    "- Be concise. Don't speculate."
)


def answer(question: str, corpus_path: str, mode: str = "smart",
           history: list | None = None, verbose: bool = False):
    """Yields content chunks. Caller decides how to display them (print, Streamlit, etc.)."""
    corpus = load(corpus_path)
    if mode == "smart":
        hits = smart_retrieve(corpus, question, budget_tokens=4000, top_k=8)
    elif mode == "all":
        hits = all_truncate(corpus, budget_tokens=8000)
    else:
        raise ValueError(f"unknown mode {mode}")

    if verbose:
        print(f"[retrieved {len(hits)} segments, mode={mode}]", file=sys.stderr)
        for h in hits[:5]:
            score = f"{h['score']:.2f}" if h["score"] is not None else "n/a"
            preview = h["text"][:80].replace("\n", " ")
            print(f"  [{score}] {h['path']}:{h['segment_id']}  {preview}...", file=sys.stderr)

    ctx = format_context(hits)
    msgs = [
        {"role": "system", "content": SYSTEM_MSG},
        {"role": "system", "content": f"Corpus context:\n\n{ctx}"},
    ]
    # bounded history (last 10 turns is the Nemotron tutorial's choice)
    if history:
        msgs.extend(history[-10:])
    msgs.append({"role": "user", "content": question})

    client, model = make_client()
    yield from stream_chat(client, model, msgs, temperature=0.2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="corpus.json")
    ap.add_argument("--mode", choices=["smart", "all"], default="smart")
    ap.add_argument("question", nargs="+")
    args = ap.parse_args()

    q = " ".join(args.question)
    for chunk in answer(q, args.corpus, mode=args.mode, verbose=True):
        print(chunk, end="", flush=True)
    print()


if __name__ == "__main__":
    main()
