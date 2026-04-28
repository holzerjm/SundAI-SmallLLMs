"""Distillation scaffold: generate a training set from a strong model, then fine-tune a tiny model.

Stage 1 (`generate`) is fully runnable. It produces a JSONL file of (question, sql) pairs by
having a strong model (default: qwen3:8b, but point at GPT-4o or Claude for better data) solve
many variations of the task.

Stage 2 (`train`) is a scaffold. The actual training loop is gated behind --actually-train and
requires `transformers`, `peft`, and `trl`. On Apple Silicon, swap in MLX-LM or Unsloth instead.
"""
import argparse
import json
import random
import sys
from pathlib import Path

from client import make_client
import task


# A few question templates for synthetic data generation. Replace with your own corpus
# or scrape real text-to-SQL benchmarks.
QUESTION_TEMPLATES = [
    "What is the {agg} {field} per {group} in {year}?",
    "Which {group} has the highest {agg} {field}?",
    "List {group}s with no {field}.",
    "Show the {agg} {field} for each month in {year}.",
    "Find the top {n} {group}s by {field}.",
]
SUBSTITUTIONS = {
    "agg": ["average", "total", "maximum", "minimum"],
    "field": ["amount", "revenue", "order count"],
    "group": ["customer", "country"],
    "year": ["2023", "2024"],
    "n": ["3", "5", "10"],
}


def synthesize_question() -> str:
    template = random.choice(QUESTION_TEMPLATES)
    out = template
    for key, opts in SUBSTITUTIONS.items():
        out = out.replace("{" + key + "}", random.choice(opts))
    return out


def cmd_generate(args):
    client = make_client()
    teacher = args.teacher
    out = Path(args.out)
    rows = []

    print(f"generating {args.n} samples using teacher={teacher}")
    seen = set()
    while len(rows) < args.n:
        q = synthesize_question()
        if q in seen:
            continue
        seen.add(q)

        try:
            sql = task.run(client, teacher, q).strip()
        except Exception as e:
            print(f"  skip: {e}")
            continue
        sql = task.extract_sql(sql)

        # accept only generations that actually run on the fixture DB
        try:
            db = task.fixture_db()
            db.execute(sql)
        except Exception:
            continue

        rows.append({"question": q, "sql": sql})
        if len(rows) % 25 == 0:
            print(f"  {len(rows)}/{args.n}")

    with out.open("w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    print(f"\nwrote {len(rows)} samples to {out}")


def cmd_train(args):
    print("Training is a scaffold — wire up your trainer of choice.\n")
    print("Recommended paths:")
    print("  - MLX-LM (Apple Silicon):    https://github.com/ml-explore/mlx-lm")
    print("  - Unsloth (NVIDIA, fast):    https://unsloth.ai")
    print("  - TRL + PEFT (general):      https://huggingface.co/docs/trl")
    print()
    print("Example MLX-LM command:")
    print(f"  mlx_lm.lora --model mlx-community/Qwen3-1.7B-4bit \\")
    print(f"              --train --data {args.data} --iters 500 --adapter-path {args.out}")
    print()
    print("After training:")
    print("  mlx_lm.fuse --model mlx-community/Qwen3-1.7B-4bit \\")
    print(f"              --adapter-path {args.out} --save-path {args.out}-fused")
    print()
    print("Then convert to GGUF and import into Ollama with `ollama create my-finetune -f Modelfile`.")

    if not args.actually_train:
        print("\n(re-run with --actually-train and install dependencies to attempt the trainer)")
        return

    try:
        from datasets import load_dataset  # noqa
        from trl import SFTTrainer  # noqa
        from peft import LoraConfig  # noqa
    except ImportError:
        print("missing deps. install: pip install transformers peft trl datasets accelerate", file=sys.stderr)
        sys.exit(1)

    # Hackathon attendees: implement the trainer here. Keep it small — a LoRA on
    # 500 samples can fine-tune a 1B model in 10–20 minutes on a single GPU.
    raise NotImplementedError("actual SFTTrainer call goes here")


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)

    g = sp.add_parser("generate", help="produce a training JSONL using a teacher model")
    g.add_argument("--n", type=int, default=200)
    g.add_argument("--teacher", default="qwen3:8b",
                   help="strong model used as teacher. Set OPENAI_BASE_URL=https://api.openai.com/v1 + --teacher gpt-4o for cloud.")
    g.add_argument("--out", default="training.jsonl")
    g.set_defaults(func=cmd_generate)

    t = sp.add_parser("train", help="scaffold for LoRA fine-tuning")
    t.add_argument("--data", required=True)
    t.add_argument("--base", default="qwen3:1.7b")
    t.add_argument("--out", default="my-finetune")
    t.add_argument("--actually-train", action="store_true")
    t.set_defaults(func=cmd_train)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
