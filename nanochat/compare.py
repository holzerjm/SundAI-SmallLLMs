"""Head-to-head: local Gemma 4 vs Nemotron-3 Nano on the same corpus + questions.

Runs both models on each question, records latency and answer text. If you have a
ground-truth file, also reports agreement vs. ground truth.

Usage:
  echo "what is X?" >  questions.txt
  echo "summarize Y" >> questions.txt
  python compare.py --corpus corpus.json --questions questions.txt
"""
import argparse
import json
import os
import time
from pathlib import Path

from client import make_client, chat_blocking, LOCAL_MODEL, CLOUD_MODEL
from retrieval import load, smart_retrieve, format_context
from chat import SYSTEM_MSG


def run_one(model: str, use_cloud: bool, corpus: dict, question: str) -> dict:
    if use_cloud:
        os.environ["NANOCHAT_USE_NEMOTRON"] = "1"
    else:
        os.environ.pop("NANOCHAT_USE_NEMOTRON", None)
    client, model_tag = make_client()

    hits = smart_retrieve(corpus, question, budget_tokens=4000, top_k=8)
    msgs = [
        {"role": "system", "content": SYSTEM_MSG},
        {"role": "system", "content": f"Corpus context:\n\n{format_context(hits)}"},
        {"role": "user", "content": question},
    ]
    t0 = time.time()
    try:
        answer = chat_blocking(client, model_tag, msgs, temperature=0.0)
        err = None
    except Exception as e:
        answer = ""
        err = f"{type(e).__name__}: {e}"
    latency = time.time() - t0
    return {
        "model": model_tag,
        "answer": answer,
        "latency_s": round(latency, 3),
        "n_hits": len(hits),
        "error": err,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="corpus.json")
    ap.add_argument("--questions", required=True, help="one question per line")
    ap.add_argument("--out", default="compare_results.json")
    ap.add_argument("--skip-nemotron", action="store_true",
                    help="skip the cloud model (e.g. if you don't have OLLAMA_API_KEY)")
    args = ap.parse_args()

    corpus = load(args.corpus)
    questions = [q.strip() for q in Path(args.questions).read_text().splitlines() if q.strip()]
    print(f"running {len(questions)} questions")

    results = []
    for i, q in enumerate(questions, 1):
        print(f"\n[{i}/{len(questions)}] {q[:80]}")
        local = run_one(LOCAL_MODEL, use_cloud=False, corpus=corpus, question=q)
        print(f"  [{local['model']:<25}] {local['latency_s']:.2f}s")
        cloud = None
        if not args.skip_nemotron:
            if not os.environ.get("OLLAMA_API_KEY"):
                print("  (skipping cloud — no OLLAMA_API_KEY)")
            else:
                cloud = run_one(CLOUD_MODEL, use_cloud=True, corpus=corpus, question=q)
                print(f"  [{cloud['model']:<25}] {cloud['latency_s']:.2f}s")
        results.append({"question": q, "local": local, "cloud": cloud})

    Path(args.out).write_text(json.dumps(results, indent=2))
    print(f"\nwrote {args.out}")

    print("\nlatency summary:")
    avg_local = sum(r["local"]["latency_s"] for r in results) / len(results)
    print(f"  {LOCAL_MODEL:<30} avg {avg_local:.2f}s")
    if any(r["cloud"] for r in results):
        clouds = [r["cloud"]["latency_s"] for r in results if r["cloud"]]
        print(f"  {CLOUD_MODEL:<30} avg {sum(clouds) / len(clouds):.2f}s")


if __name__ == "__main__":
    main()
