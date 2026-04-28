# pocketcoder

A 200-line, fully local, Claude-Code-style coding agent. Built for the SundAI Small Models Hack.

The point isn't to compete with Claude Code — it's to give you a hackable harness where you can find out where small models break, fix the prompt/tools, and ship a demo where a local model fixes a real bug offline.

## What's in here

```
pocketcoder/
├── client.py     # OpenAI-compatible client, swap base URL for any backend
├── tools.py      # read_file, write_file, edit_file, bash, grep, list_dir, finish
├── prompts.py    # system prompt — this is where most small-model wins come from
├── agent.py      # the loop: model -> tool calls -> results -> repeat
└── cli.py        # interactive REPL
```

## Step-by-step

### 1. Setup

```bash
./setup.sh
```

Pulls `gemma4:4b` by default. Edit the script for other models, or override with `POCKETCODER_MODEL=gemma4:12b python agent.py ...`.

### 2. One-shot a task from the CLI

```bash
python agent.py "Add a function is_prime(n) to mathutils.py with a unit test, then run pytest."
```

You'll see each tool call streamed. The agent stops when it calls `finish` or hits the turn limit.

### 3. Interactive mode

```bash
python cli.py
```

A REPL. Type messages, the agent edits files and runs commands, you steer.

```
> read_file pyproject.toml and tell me what test runner this project uses
[read_file] {"path": "pyproject.toml"} -> ... pytest ...
This project uses pytest.

> add a test for the is_prime function
[read_file] mathutils.py
[write_file] tests/test_mathutils.py
[bash] {"cmd": "pytest tests/test_mathutils.py"}
Tests pass. Anything else?
```

### 4. Tune for your model

Small models drop tool calls, hallucinate file paths, and stop early. The fixes live in `prompts.py`. Tweak the system prompt, run on a real task, observe where it breaks, repeat.

The most common wins:

- **Be explicit about the loop**: "After each tool call, decide if you have enough information. If not, call another tool. If yes, call `finish`."
- **Give an example trace** in the system prompt. One-shot prompting helps small models a lot.
- **Limit options**: fewer tools = higher reliability. Start with `read_file`, `write_file`, `bash` and add the rest only when needed.
- **Force structured thinking**: ask for a one-line plan before each tool call. (`prompts.PLAN_BEFORE_ACT`.)

### 5. Compare reliability vs. a bigger model

Hook this up to `smallbench`'s tool-use task. Or run the same task 10 times, count completions:

```bash
for i in $(seq 1 10); do
  python agent.py "rename foo to bar in src/" > runs/$i.log 2>&1
done
grep -l "FINISH" runs/*.log | wc -l
```

## Suggested challenges

1. **Pocket Code Agent** — Pick a real GitHub bug, fix it end-to-end with this harness running entirely on a laptop, record the demo.
2. **Prompt vs. Model** — How much can you close the gap to Sonnet by tuning `prompts.py`? Measure with `smallbench`.
3. **Token-efficient tools** — Replace `read_file` with `read_file_lines(path, start, end)` and a `grep` tool. Measure context savings on a real refactor.
4. **Plan-then-act** — Add a "planner" pass that produces a numbered checklist before any tools run. Does it improve completion rate?
5. **Multi-model conductor** — Use the small model for tool calls and a tiny model for retries on validation errors. Measure throughput.
6. **OpenAI-compatible proxy for Claude Code** — Wrap your local model in a server that accepts Claude Code's requests. Then run Claude Code against the local model and find the prompt/tool gaps.

## How small-model agents differ from large-model agents

| | Large model | Small model |
|---|---|---|
| Tool schemas | Reads them once, gets them | Drift halfway through; re-state in prompt |
| Long context | Stays coherent at 200k+ | Falls apart past ~32k; compact aggressively |
| Multi-step plans | Self-corrects from errors | Often loops — needs explicit "if X happens, do Y" |
| File paths | Almost never hallucinated | Hallucinates often — verify with `list_dir` first |
| Tool count | 20+ tools fine | 5–7 tools is the sweet spot |

These are the prompts/tools choices to get right. Almost every "small models can't do agentic" failure is actually a harness problem.
