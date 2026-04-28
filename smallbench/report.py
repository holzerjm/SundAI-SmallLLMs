"""Print a side-by-side comparison table from one or more bench.py result files."""
import json
import sys
from collections import defaultdict
from pathlib import Path

from rich.console import Console
from rich.table import Table


def load(path: str) -> dict:
    return json.loads(Path(path).read_text())


def main():
    if len(sys.argv) < 2:
        print("usage: python report.py <results.json> [<more.json> ...]")
        sys.exit(1)

    runs = [load(p) for p in sys.argv[1:]]
    models = [r["model"] for r in runs]

    # task_id -> {model -> (passes, total, avg_latency)}
    grid: dict[str, dict[str, tuple[int, int, float]]] = defaultdict(dict)
    for run in runs:
        for r in run["results"]:
            trials = r["trials"]
            passes = sum(1 for t in trials if t["pass"])
            total = len(trials)
            avg_lat = sum(t["latency_s"] for t in trials) / total
            grid[r["task_id"]][run["model"]] = (passes, total, avg_lat)

    table = Table(title="smallbench results")
    table.add_column("Task", style="bold")
    for m in models:
        table.add_column(m)

    for task_id in sorted(grid):
        row = [task_id]
        for m in models:
            cell = grid[task_id].get(m)
            if cell is None:
                row.append("-")
            else:
                p, t, lat = cell
                row.append(f"{p}/{t} ({lat:.2f}s)")
        table.add_row(*row)

    overall = []
    for m in models:
        total_p = sum(grid[t][m][0] for t in grid if m in grid[t])
        total_t = sum(grid[t][m][1] for t in grid if m in grid[t])
        overall.append(f"{100 * total_p / total_t:.0f}%" if total_t else "-")
    table.add_row("[bold]overall[/bold]", *overall)

    Console().print(table)


if __name__ == "__main__":
    main()
