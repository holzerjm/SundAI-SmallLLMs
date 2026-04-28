"""Small-first router: try a tiny model, validate, escalate to a bigger one only if needed.

The point is to spend the bigger model's compute only on hard queries.
"""
import argparse
import time

from client import make_client
import task


SMALL = "gemma4:1b"
BIG = "gemma4:4b"


def validate(t: dict, response: str) -> bool:
    """Same grader as smallbench. Replace with task-specific validation if you have one."""
    ok, _ = task.grade(t, response)
    return ok


def route(client, t: dict, verbose: bool = True) -> dict:
    """Try small first. Escalate to big on validation failure."""
    t0 = time.time()
    small_resp = task.run(client, SMALL, t["question"])
    small_latency = time.time() - t0

    if validate(t, small_resp):
        if verbose:
            print(f"  [{SMALL}] OK ({small_latency:.2f}s)")
        return {
            "model": SMALL, "response": small_resp, "escalated": False,
            "latency_s": small_latency,
        }

    if verbose:
        print(f"  [{SMALL}] failed ({small_latency:.2f}s) -> escalating")
    t1 = time.time()
    big_resp = task.run(client, BIG, t["question"])
    big_latency = time.time() - t1
    return {
        "model": BIG, "response": big_resp, "escalated": True,
        "latency_s": small_latency + big_latency,
    }


def benchmark(client):
    """Run all tasks and compare router vs. always-small vs. always-big."""
    rows = []
    for t in task.TASKS:
        # always-small
        t0 = time.time()
        small_resp = task.run(client, SMALL, t["question"])
        small_lat = time.time() - t0
        small_ok = validate(t, small_resp)

        # always-big
        t0 = time.time()
        big_resp = task.run(client, BIG, t["question"])
        big_lat = time.time() - t0
        big_ok = validate(t, big_resp)

        # router (re-uses the small_resp we already have)
        if small_ok:
            router_lat = small_lat
            router_escalated = False
            router_ok = True
        else:
            t0 = time.time()
            big_resp_2 = task.run(client, BIG, t["question"])
            router_lat = small_lat + (time.time() - t0)
            router_escalated = True
            router_ok = validate(t, big_resp_2)

        rows.append({
            "task": t["id"],
            "small_ok": small_ok, "small_lat": small_lat,
            "big_ok": big_ok, "big_lat": big_lat,
            "router_ok": router_ok, "router_lat": router_lat,
            "router_escalated": router_escalated,
        })

    n = len(rows)
    print(f"\n{'Task':<35} {'small':<8} {'big':<8} {'router':<10} {'esc?'}")
    for r in rows:
        print(f"{r['task']:<35} "
              f"{('PASS' if r['small_ok'] else 'FAIL'):<8} "
              f"{('PASS' if r['big_ok'] else 'FAIL'):<8} "
              f"{('PASS' if r['router_ok'] else 'FAIL'):<10} "
              f"{'yes' if r['router_escalated'] else 'no'}")

    print()
    print(f"small-only:  {100 * sum(r['small_ok'] for r in rows) / n:.0f}%  avg {sum(r['small_lat'] for r in rows) / n:.2f}s")
    print(f"big-only:    {100 * sum(r['big_ok'] for r in rows) / n:.0f}%  avg {sum(r['big_lat'] for r in rows) / n:.2f}s")
    print(f"router:      {100 * sum(r['router_ok'] for r in rows) / n:.0f}%  avg {sum(r['router_lat'] for r in rows) / n:.2f}s  "
          f"escalation rate {100 * sum(r['router_escalated'] for r in rows) / n:.0f}%")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("question", nargs="*")
    ap.add_argument("--benchmark", action="store_true")
    args = ap.parse_args()

    client = make_client()
    if args.benchmark:
        benchmark(client)
        return

    if not args.question:
        print("usage: python router.py 'your question'  or  python router.py --benchmark")
        return

    q = " ".join(args.question)
    fake_task = {"question": q, "reference_sql": "SELECT 1"}  # no validation for ad-hoc queries
    r = route(client, fake_task, verbose=True)
    print(f"\nmodel used: {r['model']}")
    print(f"latency: {r['latency_s']:.2f}s")
    print(f"\nresponse:\n{r['response']}")


if __name__ == "__main__":
    main()
