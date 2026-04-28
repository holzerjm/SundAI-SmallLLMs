# shrinkray

Three experiments for making small models go further: quantization comparison, model routing, and a distillation scaffold. Built for the SundAI Small Models Hack.

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

Pulls multiple quantizations of `qwen3:8b` and a stronger reference model. Edit if you want different models or different quant levels.

### 2. Quantization comparison

How much does aggressive quantization hurt task performance?

```bash
python quant_compare.py
```

This runs the task across each quant level and reports pass rate, tok/s, and disk size:

```
Model                  Pass rate   Tok/s   Disk
qwen3:8b-fp16          92%         18.2    16.1 GB
qwen3:8b-q8_0          91%         28.7    8.6 GB
qwen3:8b-q4_K_M        88%         42.1    4.9 GB
qwen3:8b-q3_K_S        76%         48.3    3.7 GB   <- cliff starts here
```

### 3. Model routing

Use the small model first, escalate to a bigger model only when needed:

```bash
python router.py "What's the average order value by customer in 2024?"
```

The router runs the task on the small model, validates the output (in this case, parses the SQL and runs it against the schema), and only escalates if validation fails. Compare end-to-end latency and "cloud cost" (escalation rate) against using the big model for everything:

```bash
python router.py --benchmark
```

### 4. Distillation scaffold

Generate a training set by having a strong model solve the task, then fine-tune a tiny model to match:

```bash
# stage 1: generate (this hits the strong model — set OPENAI_API_KEY for cloud,
# or point to a stronger local model)
python distill.py generate --n 500 --out training.jsonl

# stage 2: review
head training.jsonl

# stage 3: fine-tune (scaffold only — see distill.py for the trainer code)
python distill.py train --data training.jsonl --base qwen3:1.7b --out my-finetune
```

The actual training code is gated behind an `--actually-train` flag and requires `transformers`, `peft`, `trl`, and a GPU (or use [unsloth](https://unsloth.ai) / [MLX-LM](https://github.com/ml-explore/mlx-lm) on Apple Silicon).

## Suggested challenges

1. **Quantization Wars** — Find the most aggressive quant of your favorite model that maintains task performance. Build a leaderboard.
2. **Cost-Optimal Router** — Tune the router to match Sonnet quality at <30% of the cost or latency. Plot the Pareto frontier.
3. **Specialist Distillation** — Pick a narrow task (regex generation, log parsing, schema migration). Distill a 1B model that beats the 30B base on it. Report a 100× speedup.
4. **Speculative Decoding** — Combine a tiny draft model and the same model at full size. Implement (or wire up) speculative decoding via vLLM / llama.cpp. Report the decode speedup.
5. **Multi-Agent on a Budget** — Run 3 specialized small models concurrently (planner / coder / critic) and beat a single larger model on a real task. Memory budget: 32GB.
6. **The Smallest Useful Model** — How small can you go while staying above the "useful" threshold for your task? 1B? 500M? 100M? Find the actual limit.

## Why these three experiments?

They're the levers you actually have when small models aren't quite good enough:

- **Quantize less** if you have headroom — quality recovery is cheap.
- **Route to a bigger model** if some queries are hard and others aren't — you pay for the hard ones only.
- **Distill** if the task is narrow and you need both speed and quality — turns a 30B model into a 1B model for a fixed task.

Each one is an interesting hackathon project on its own. Combined, they're a genuine production strategy.
