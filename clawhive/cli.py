"""Interactive REPL — talk to the swarm directly. No ZeroClaw required."""
import sys

from orchestrator import run, summary, render
from client import planner_spec, coder_spec, critic_spec


def main():
    print(f"clawhive REPL")
    print(f"  planner: {planner_spec().label}")
    print(f"  coder:   {coder_spec().label}")
    print(f"  critic:  {critic_spec().label}")
    print(f"  ctrl-d to exit\n")

    while True:
        try:
            task = input("task> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not task:
            continue
        try:
            plan_obj = run(task)
        except Exception as e:
            print(f"\n[error] {type(e).__name__}: {e}\n")
            continue
        summary(plan_obj)
        try:
            show = input("\nshow assembled output? [y/N] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if show == "y":
            print(render(plan_obj))
        print()


if __name__ == "__main__":
    main()
