#!/usr/bin/env python3
"""CLI bridge between ZeroClaw and the clawhive Python orchestrator.

ZeroClaw's `[[tools]]` shell-tool config calls this script with one of:
  agent_tools.py delegate "the full task description"
  agent_tools.py status

Stdout is what gets returned to the ZeroClaw conductor (and the user).
"""
import argparse
import sys
from pathlib import Path

# add the parent clawhive/ dir to the path so we can import the orchestrator
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from orchestrator import run, render, summary
from client import planner_spec, coder_spec, critic_spec


def cmd_delegate(args):
    plan_obj = run(args.task, verbose=False)

    n_passed = sum(1 for s in plan_obj.steps if s.passed)
    n_total = len(plan_obj.steps)

    out = []
    out.append(f"swarm done: {n_passed}/{n_total} steps passed, "
               f"${plan_obj.total_cost_usd:.4f} frontier cost\n")
    out.append("---")
    out.append(render(plan_obj))
    print("\n".join(out))


def cmd_status(args):
    """Tells the conductor what models are wired in. Useful for `/status` style commands."""
    print(f"clawhive swarm:")
    print(f"  planner: {planner_spec().label}")
    print(f"  coder:   {coder_spec().label}")
    print(f"  critic:  {critic_spec().label}")


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)

    d = sp.add_parser("delegate")
    d.add_argument("task")
    d.set_defaults(func=cmd_delegate)

    s = sp.add_parser("status")
    s.set_defaults(func=cmd_status)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
