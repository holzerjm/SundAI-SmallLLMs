"""Lexical retrieval over a corpus.json. No embeddings, no vector DB, no GPU.

Two modes:

  smart:  score segments by keyword overlap with the query, take the top-k.
  all:    pack as much of the corpus as fits in the budget, in document order.

The smart scorer is a simplified BM25 — a real BM25 with IDF would be better, and
adding it is one of the suggested challenges.
"""
import json
import math
from collections import Counter
from pathlib import Path

from corpus import tokenize


def load(path: str) -> dict:
    return json.loads(Path(path).read_text())


def score_segment(query_tokens: list[str], seg_tokens: list[str], df: Counter, n_segments: int) -> float:
    """TF-IDF-flavored score. Higher is better."""
    if not seg_tokens:
        return 0.0
    seg_counts = Counter(seg_tokens)
    score = 0.0
    for q in set(query_tokens):
        if q not in seg_counts:
            continue
        tf = seg_counts[q] / len(seg_tokens)
        idf = math.log((n_segments + 1) / (df.get(q, 0) + 1)) + 1.0
        score += tf * idf
    return score


def smart_retrieve(corpus: dict, query: str, budget_tokens: int = 4000, top_k: int = 8) -> list[dict]:
    """Pick the best-scoring segments that fit within the token budget."""
    qtoks = tokenize(query)
    if not qtoks:
        return []
    segs = corpus["segments"]
    n = len(segs)
    df = Counter()
    for s in segs:
        for t in set(s["tokens"]):
            df[t] += 1

    scored = [(score_segment(qtoks, s["tokens"], df, n), s) for s in segs]
    scored.sort(key=lambda x: -x[0])

    out = []
    used = 0
    for score, s in scored[:top_k * 4]:  # consider more than top_k in case some don't fit
        if score <= 0:
            break
        if used + s["approx_tokens"] > budget_tokens:
            continue
        out.append({"score": score, **s})
        used += s["approx_tokens"]
        if len(out) >= top_k:
            break
    return out


def all_truncate(corpus: dict, budget_tokens: int = 8000) -> list[dict]:
    """Pack segments in document order until the budget is hit. No scoring."""
    out = []
    used = 0
    for s in corpus["segments"]:
        if used + s["approx_tokens"] > budget_tokens:
            break
        out.append({"score": None, **s})
        used += s["approx_tokens"]
    return out


def format_context(hits: list[dict]) -> str:
    """The context block we hand to the model. Each segment is preceded by a citation tag."""
    return "\n\n".join(f"[{h['path']}:{h['segment_id']}]\n{h['text']}" for h in hits)
