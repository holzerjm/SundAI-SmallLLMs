"""Example: solve a single coding task end-to-end and print the assembled output.

Run:
  python examples/coding_task.py
"""
import sys
from pathlib import Path

# allow running from the examples/ dir
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from orchestrator import run, summary, render


TASK = (
    "Build a small Python script `top_hn.py` that fetches the top 10 Hacker News stories "
    "via the public Firebase API at https://hacker-news.firebaseio.com/v0/topstories.json, "
    "fetches each story's title and URL, and prints them as a numbered markdown list."
)


def main():
    plan_obj = run(TASK)
    summary(plan_obj)
    print("\n" + "=" * 72)
    print("ASSEMBLED OUTPUT")
    print("=" * 72)
    print(render(plan_obj))


if __name__ == "__main__":
    main()
