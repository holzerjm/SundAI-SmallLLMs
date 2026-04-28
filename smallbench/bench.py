"""Run every task in tasks/ against a model. Saves a JSON results file."""
import argparse
import importlib
import json
import pkgutil
import time
from pathlib import Path

from client import make_client, chat
import tasks


def discover_tasks() -> list[dict]:
    """Auto-load every TASKS list exported by tasks/*.py."""
    out = []
    for mod in pkgutil.iter_modules(tasks.__path__):
        m = importlib.import_module(f"tasks.{mod.name}")
        for t in getattr(m, "TASKS", []):
            t = {**t, "id": f"{mod.name}/{t['id']}"}
            out.append(t)
    return out


def run_one(client, model: str, task: dict) -> dict:
    msgs = [{"role": "user", "content": task["prompt"]}]
    kw = {}
    if "tools" in task:
        kw["tools"] = task["tools"]
    t0 = time.time()
    try:
        resp = chat(client, model, msgs, **kw).choices[0].message
    except Exception as e:
        return {"pass": False, "reason": f"api error: {e}", "latency_s": time.time() - t0}
    latency = time.time() - t0
    passed, reason = task["grader"](resp)
    return {
        "pass": passed,
        "reason": reason,
        "latency_s": round(latency, 3),
        "content": (resp.content or "")[:500],
        "tool_calls": [
            {"name": tc.function.name, "args": tc.function.arguments}
            for tc in (resp.tool_calls or [])
        ],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--base-url", default=None)
    ap.add_argument("--trials", type=int, default=3)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    client = make_client(args.base_url)
    all_tasks = discover_tasks()
    print(f"running {len(all_tasks)} tasks x {args.trials} trials against {args.model}")

    results = []
    for task in all_tasks:
        trials = [run_one(client, args.model, task) for _ in range(args.trials)]
        passes = sum(1 for t in trials if t["pass"])
        avg_latency = sum(t["latency_s"] for t in trials) / len(trials)
        print(f"  {task['id']}: {passes}/{args.trials}  avg {avg_latency:.2f}s")
        results.append({"task_id": task["id"], "trials": trials})

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps({"model": args.model, "results": results}, indent=2))
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
