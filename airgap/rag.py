"""Retrieve top-k chunks for a query and ask the model with citations."""
import argparse
import json
from pathlib import Path

import numpy as np

from client import make_client, embed, chat


SYSTEM = """You answer questions using ONLY the provided context. Each context chunk is preceded by [path:chunk_id].

Rules:
- Cite the source for every factual claim, e.g. "The setup is local-only [README.md:0]."
- If the context does not contain the answer, say so explicitly. Do not invent details.
- Be concise.
"""


def load_index(path: str) -> dict:
    data = json.loads(Path(path).read_text())
    data["matrix"] = np.array([r["embedding"] for r in data["records"]], dtype=np.float32)
    # normalize for cosine via dot product
    norms = np.linalg.norm(data["matrix"], axis=1, keepdims=True)
    data["matrix"] = data["matrix"] / np.clip(norms, 1e-12, None)
    return data


def search(index: dict, query_vec: list[float], k: int = 5) -> list[dict]:
    q = np.array(query_vec, dtype=np.float32)
    q = q / max(float(np.linalg.norm(q)), 1e-12)
    scores = index["matrix"] @ q
    top = np.argsort(-scores)[:k]
    return [{"score": float(scores[i]), **index["records"][i]} for i in top]


def format_context(hits: list[dict]) -> str:
    return "\n\n".join(f"[{h['path']}:{h['chunk_id']}]\n{h['text']}" for h in hits)


def answer(client, index: dict, question: str, k: int = 5, verbose: bool = False) -> tuple[str, list[dict]]:
    qvec = embed(client, [question])[0]
    hits = search(index, qvec, k=k)
    if verbose:
        for h in hits:
            print(f"  [{h['score']:.3f}] {h['path']}:{h['chunk_id']} {h['text'][:80]}...")
    msgs = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": f"Context:\n{format_context(hits)}\n\nQuestion: {question}"},
    ]
    return chat(client, msgs), hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", default="index.json")
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("question", nargs="+")
    args = ap.parse_args()

    client = make_client()
    index = load_index(args.index)
    print(f"loaded {len(index['records'])} chunks from {args.index}\n")
    print("retrieved:")
    out, _ = answer(client, index, " ".join(args.question), k=args.k, verbose=True)
    print("\nanswer:")
    print(out)


if __name__ == "__main__":
    main()
