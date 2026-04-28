"""The Plan → Act → Critique loop. Wire frontier planning to local execution.

Usage:
  python orchestrator.py "your task here"
  python orchestrator.py --benchmark
"""
import argparse
import sys
import time

from agents import Plan, plan, code, critique
from client import planner_spec, coder_spec, critic_spec


MAX_RETRIES_PER_STEP = 2


def run(task: str, verbose: bool = True) -> Plan:
    plan_obj = Plan(task=task, steps=[])
    if verbose:
        print(f"\n[task] {task}\n")
        print(f"[planner    @ {planner_spec().label:<30}] thinking...")

    plan_obj.steps = plan(task, plan_obj)
    if verbose:
        print(f"[planner    @ {planner_spec().label:<30}] {len(plan_obj.steps)} steps planned")
        for s in plan_obj.steps:
            print(f"  {s.n}. {s.description}")
        print()

    for step in plan_obj.steps:
        for attempt in range(MAX_RETRIES_PER_STEP + 1):
            if verbose:
                tag = "implementing" if attempt == 0 else f"retry {attempt}"
                print(f"[coder      @ {coder_spec().label:<30}] step {step.n}: {tag}...")
            step.output = code(task, step, plan_obj.steps[:step.n - 1], plan_obj)
            ok, reason = critique(step, plan_obj)
            step.passed = ok
            step.feedback = reason
            if verbose:
                status = "PASS" if ok else f"FAIL — {reason}"
                print(f"[critic     @ {critic_spec().label:<30}] step {step.n}: {status}")
            if ok:
                break
            step.retries += 1
        if verbose:
            print()

    return plan_obj


def render(plan_obj: Plan) -> str:
    """Assemble the final output: concatenate all step outputs."""
    return "\n\n".join(f"# Step {s.n}: {s.description}\n{s.output}"
                       for s in plan_obj.steps if s.passed)


def summary(plan_obj: Plan):
    n_passed = sum(1 for s in plan_obj.steps if s.passed)
    n_total = len(plan_obj.steps)
    n_retries = sum(s.retries for s in plan_obj.steps)
    print(f"\n[summary]")
    print(f"  {n_passed}/{n_total} steps passed, {n_retries} retries total")
    print(f"  estimated frontier cost: ${plan_obj.total_cost_usd:.4f}")
    by_role = {}
    for role, label, usage in plan_obj.spec_log:
        key = (role, label)
        by_role[key] = by_role.get(key, [0, 0])
        by_role[key][0] += usage["input_tokens"]
        by_role[key][1] += usage["output_tokens"]
    for (role, label), (in_t, out_t) in by_role.items():
        print(f"  {role:<10} {label:<35} in={in_t:>6}  out={out_t:>6}")


# ---------- benchmark ----------

BENCHMARK_TASKS = [
    "Write a function that downloads a URL and returns the HTTP status code, with a 5-second timeout.",
    "Write a CLI that takes a directory path and prints a histogram of file extensions.",
    "Implement a function `merge_intervals(intervals)` that merges overlapping intervals.",
    "Write a script that reads a CSV and outputs the same data as JSON, preserving column order.",
]


def benchmark():
    print("=" * 72)
    print("running benchmark suite")
    print(f"  planner: {planner_spec().label}")
    print(f"  coder:   {coder_spec().label}")
    print(f"  critic:  {critic_spec().label}")
    print("=" * 72)

    total_cost = 0.0
    total_time = 0.0
    pass_counts = []
    for task in BENCHMARK_TASKS:
        t0 = time.time()
        try:
            p = run(task, verbose=False)
        except Exception as e:
            print(f"[FAIL] {task[:50]}... -> {e}")
            continue
        elapsed = time.time() - t0
        total_time += elapsed
        total_cost += p.total_cost_usd
        n_passed = sum(1 for s in p.steps if s.passed)
        n_total = len(p.steps)
        pass_counts.append((n_passed, n_total))
        print(f"  [{n_passed}/{n_total} steps, {elapsed:.1f}s, ${p.total_cost_usd:.4f}] {task[:50]}...")

    print("=" * 72)
    print(f"  total time:  {total_time:.1f}s")
    print(f"  total cost:  ${total_cost:.4f}")
    if pass_counts:
        rate = sum(p / t for p, t in pass_counts) / len(pass_counts)
        print(f"  step pass:   {rate * 100:.0f}%")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("task", nargs="*")
    ap.add_argument("--benchmark", action="store_true")
    ap.add_argument("--render", action="store_true", help="print assembled output at the end")
    args = ap.parse_args()

    if args.benchmark:
        benchmark()
        return

    if not args.task:
        print("usage: python orchestrator.py 'your task'    or   python orchestrator.py --benchmark")
        sys.exit(1)

    plan_obj = run(" ".join(args.task))
    summary(plan_obj)
    if args.render:
        print("\n" + "=" * 72 + "\nFINAL OUTPUT\n" + "=" * 72)
        print(render(plan_obj))


if __name__ == "__main__":
    main()
