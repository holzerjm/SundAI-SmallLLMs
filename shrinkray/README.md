# shrinkray

Three experiments for making small models go further: quantization comparison, model routing, and a distillation scaffold. Built for the SundAI Small Models Hack, defaulting to **Google Gemma 4**.

## What's in here

```
shrinkray/
├── client.py          # OpenAI-compatible client
├── task.py            # the SQL-gen task all three experiments share
├── quant_compare.py   # benchmark different quants of the same model
├── router.py          # small-first, escalate-to-big router
└── distill.py         # generate training data + fine-tune scaffold
```

All three experiments target the same task in `task.py` so you can compare apples to apples: "given a natural-language question over a known schema, generate correct SQL." Swap the task for whatever you care about.

## Step-by-step

### 1. Setup

```bash
./setup.sh
```

Pulls `gemma4:1b` and `gemma4:4b` (with multiple quantizations of the latter) for the experiments. Edit if you want different models or different quant levels.

### 2. Quantization comparison

How much does aggressive quantization hurt task performance?

```bash
python quant_compare.py
```

This runs the task across each quant level and reports pass rate, latency, and disk size. Example shape (numbers will vary by hardware and exact tag):

```
Model                    Pass rate   Avg latency   Disk
gemma4:4b-fp16           92%         1.85s         8.0 GB
gemma4:4b-q8_0           91%         1.10s         4.3 GB
gemma4:4b-q4_K_M         88%         0.72s         2.5 GB
gemma4:4b-q3_K_S         76%         0.65s         1.9 GB   <- cliff starts here
```

### 3. Model routing

Use the small model first, escalate to a bigger model only when needed:

```bash
python router.py "What's the average order value by customer in 2024?"
```

The router runs the task on `gemma4:1b`, validates the output (in this case, parses the SQL and runs it against the schema), and only escalates to `gemma4:4b` if validation fails. Compare end-to-end latency and "cloud cost" (escalation rate) against using the big model for everything:

```bash
python router.py --benchmark
```

### 4. Distillation scaffold

Generate a training set by having a strong model solve the task, then fine-tune a tiny model to match:

```bash
# stage 1: generate (defaults to gemma4:4b as teacher; set OPENAI_API_KEY for cloud,
# or pass --teacher gemma4:12b for a stronger local teacher)
python distill.py generate --n 500 --out training.jsonl

# stage 2: review
head training.jsonl

# stage 3: fine-tune (scaffold only — see distill.py for the trainer command)
python distill.py train --data training.jsonl --base gemma4:1b --out my-finetune
```

The actual training code is gated behind an `--actually-train` flag and requires `transformers`, `peft`, `trl`, and a GPU (or use [unsloth](https://unsloth.ai) / [MLX-LM](https://github.com/ml-explore/mlx-lm) on Apple Silicon).

## Suggested challenges

1. **Quantization Wars** — Find the most aggressive quant of Gemma 4 4B (or 12B) that maintains task performance. Build a leaderboard.
2. **Cost-Optimal Router** — Tune the router to match Sonnet quality at <30% of the cost or latency. Plot the Pareto frontier across `gemma4:1b`, `gemma4:4b`, `gemma4:12b`.
3. **Specialist Distillation** — Pick a narrow task (regex generation, log parsing, schema migration). Distill `gemma4:1b` to beat `gemma4:12b` on it. Report a 10× speedup and the quality cost.
4. **Speculative Decoding** — Combine `gemma4:1b` as a draft model with `gemma4:4b` (or 12B) as the verifier. Implement (or wire up) speculative decoding via vLLM / llama.cpp. Report the decode speedup.
5. **Multi-Agent on a Budget** — Run 3 specialized small models concurrently (planner / coder / critic) and beat a single larger model on a real task. Memory budget: 32GB.
6. **The Smallest Useful Model** — How small can you go while staying above the "useful" threshold for your task? `gemma4:1b`? Distilled 500M? Find the actual limit.

## Why these three experiments?

They're the levers you actually have when small models aren't quite good enough:

- **Quantize less** if you have headroom — quality recovery is cheap.
- **Route to a bigger model** if some queries are hard and others aren't — you pay for the hard ones only.
- **Distill** if the task is narrow and you need both speed and quality — turns a 12B model into a 1B model for a fixed task.

Each one is an interesting hackathon project on its own. Combined, they're a genuine production strategy.
