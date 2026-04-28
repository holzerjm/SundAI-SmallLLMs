"""Run task.py against multiple quants and report quality + latency + size."""
import argparse
import json
import subprocess
import time

from client import make_client
import task


def disk_size_gb(model_tag: str) -> float | None:
    """Best-effort: parse `ollama list` for the size of a tag."""
    try:
        r = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=10)
    except Exception:
        return None
    for line in r.stdout.splitlines():
        if line.startswith(model_tag + " ") or line.startswith(model_tag + "\t"):
            for tok in line.split():
                if tok.endswith("GB"):
                    try:
                        return float(tok[:-2])
                    except ValueError:
                        pass
                if tok.endswith("MB"):
                    try:
                        return float(tok[:-2]) / 1024
                    except ValueError:
                        pass
    return None


def run_one(client, model: str) -> dict:
    passes = 0
    total_latency = 0.0
    failures = []
    for t in task.TASKS:
        t0 = time.time()
        try:
            resp = task.run(client, model, t["question"])
        except Exception as e:
            failures.append({"task": t["id"], "reason": f"api error: {e}"})
            continue
        latency = time.time() - t0
        total_latency += latency
        ok, reason = task.grade(t, resp)
        if ok:
            passes += 1
        else:
            failures.append({"task": t["id"], "reason": reason, "response": resp[:200]})
    return {
        "model": model,
        "pass_rate": passes / len(task.TASKS),
        "avg_latency_s": total_latency / len(task.TASKS),
        "disk_gb": disk_size_gb(model),
        "failures": failures,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--models",
        nargs="+",
        default=["gemma4:4b", "gemma4:4b-q4_K_M", "gemma4:4b-q8_0", "gemma4:1b"],
        help="Ollama tags to compare. Skip silently if a tag isn't pulled.",
    )
    ap.add_argument("--out", default="quant_results.json")
    args = ap.parse_args()

    client = make_client()
    results = []
    for m in args.models:
        print(f"running {m}...")
        try:
            results.append(run_one(client, m))
        except Exception as e:
            print(f"  skipped {m}: {e}")

    with open(args.out, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n{'Model':<25} {'Pass rate':<11} {'Avg latency':<13} {'Disk':<8}")
    for r in results:
        size = f"{r['disk_gb']:.1f} GB" if r["disk_gb"] is not None else "?"
        print(f"{r['model']:<25} {r['pass_rate'] * 100:>5.0f}%      {r['avg_latency_s']:>5.2f}s       {size}")
    print(f"\nfull results in {args.out}")


if __name__ == "__main__":
    main()
