# smallbench

A tiny, hackable eval harness for comparing local LLMs on real tasks. Built for the SundAI Small Models Hack.

Defaults to **Google Gemma 4**. Swap to any OpenAI-compatible model with `--model` and `--base-url`.

## What's in here

```
smallbench/
├── client.py          # one OpenAI-compatible client used everywhere
├── bench.py           # run tasks against a model, save JSON results
├── report.py          # turn results JSON into a comparison table
└── tasks/
    ├── coding.py      # implement-this-function tasks with executable graders
    ├── tool_use.py    # measure schema-valid tool calls
    └── extraction.py  # JSON extraction from messy text
```

## Step-by-step

### 1. Setup (60 seconds)

```bash
./setup.sh
```

This installs Python deps and pulls two Gemma 4 sizes (`gemma4:4b`, `gemma4:1b`). Edit the script for other models.

### 2. Run the baseline

```bash
python bench.py --model gemma4:4b --out results/gemma4-4b.json
python bench.py --model gemma4:1b --out results/gemma4-1b.json
```

Each run executes every task in `tasks/` 3 times (configurable with `--trials`) and writes a JSON file with per-trial outputs, latencies, and pass/fail.

### 3. Generate a report

```bash
python report.py results/*.json
```

Prints a side-by-side table:

```
Task              gemma4:4b   gemma4:1b
coding/fizzbuzz   3/3 (1.2s)  2/3 (0.5s)
coding/palindrome 3/3 (0.9s)  3/3 (0.4s)
tool_use/weather  3/3 (1.1s)  1/3 (0.4s)
extraction/person 3/3 (0.8s)  3/3 (0.3s)
overall           100%        75%
```

### 4. Add your own task

Drop a new file in `tasks/` that exposes a `TASKS` list. Each task is a dict with:

- `id`: unique string
- `prompt`: what to send the model
- `grader(response: str) -> tuple[bool, str]`: returns (pass, reason)
- optional `tools`: OpenAI-style tool schemas if the task requires tool calls

`bench.py` auto-discovers anything in `tasks/`, so just add the file.

### 5. Compare against a cloud model (optional)

```bash
OPENAI_BASE_URL=https://api.openai.com/v1 OPENAI_API_KEY=sk-... \
  python bench.py --model gpt-4o-mini --out results/gpt-4o-mini.json
```

Or against Anthropic via an OpenAI-compatible proxy. The point is to see how close Gemma 4 gets.

## Suggested challenges

Pick one and ship by demo time:

1. **The Coding Gauntlet** — Replace `tasks/coding.py` with 50 real GitHub issues. Score by whether the patch passes the original test suite. Bonus: graph quality vs. context length across `gemma4:1b`, `gemma4:4b`, `gemma4:12b`.
2. **Tool-Use Reliability** — Expand `tasks/tool_use.py` to a 200-trace eval with multi-step tool chains. Measure schema-valid rate, retry count, and end-to-end task success.
3. **Latency-That-Matters** — Add a `--measure-ttft` flag to `bench.py` that records time-to-first-token separately from decode rate. Produce a "what hardware do I need" cheat sheet.
4. **Refusal & Drift Audit** — Add `tasks/refusal.py` with 100 benign-but-touchy prompts. Measure refusal rate per Gemma 4 size.
5. **Quantization Sweep** — Pull `gemma4:4b-q4_K_M`, `gemma4:4b-q8_0`, and `gemma4:4b-fp16`. Show the quality cliff (if any).

## Adding a model from outside Ollama

Point `--base-url` at any OpenAI-compatible endpoint:

```bash
python bench.py --model my-model --base-url http://localhost:8000/v1
```

llama.cpp's server, vLLM, LM Studio, and most local serving stacks expose this by default.
