# clawhive

**Advanced track.** A multi-agent system where a frontier model plans, local Gemma 4 workers execute, and a tiny local critic reviews — all wired together by a [ZeroClaw](https://github.com/zeroclaw-labs/zeroclaw) chat agent that the user actually talks to.

This is the track for teams who want to learn three things at once:

1. **Multi-agent orchestration** — Plan / Act / Critique loops, not just a single tool-calling agent.
2. **Mixed-tier model use** — Frontier Claude for the hard reasoning, local Gemma 4 for the bulk of the tokens, tiny Gemma 4 1B for cheap reviews. The interesting question is *where the line should be*.
3. **A real chat surface** — ZeroClaw gives you a chat-everywhere agent (CLI, Discord, Telegram, webhook) without writing the harness yourself. You bring the brains; ZeroClaw brings the I/O.

## Architecture

```
                 user (CLI / Discord / webhook)
                              │
                              ▼
                     ┌─────────────────┐
                     │   ZeroClaw      │  ← chat surface, channels, memory
                     │   conductor     │
                     └────────┬────────┘
                              │ shell tool
                              ▼
                     ┌─────────────────┐
                     │  orchestrator   │  ← Python: Plan → Act → Critique
                     └───┬─────┬─────┬─┘
              ┌──────────┘     │     └──────────┐
              ▼                ▼                ▼
       ┌────────────┐   ┌────────────┐   ┌────────────┐
       │  planner   │   │   coder    │   │  critic    │
       │ Claude 4.5 │   │ gemma4:4b  │   │ gemma4:1b  │
       │ (frontier) │   │  (local)   │   │  (local)   │
       └────────────┘   └────────────┘   └────────────┘
```

The Python orchestrator (`orchestrator.py`) is the brain. ZeroClaw is the body — it gives you the chat UX, channel adapters, and a daemon mode without writing any Rust. If you don't care about the chat surface, you can run `orchestrator.py` directly.

## What's in here

```
clawhive/
├── client.py                # OpenAI-compatible client factory (local + Anthropic + OpenAI)
├── agents.py                # one function per specialized agent (planner/coder/critic/researcher)
├── orchestrator.py          # the Plan → Act → Critique loop
├── cli.py                   # interactive REPL — talk to the swarm directly
├── examples/
│   └── coding_task.py       # demo: solve a coding problem with the swarm
└── zeroclaw/
    ├── README.md            # how to wire the orchestrator into ZeroClaw
    ├── zeroclaw.toml        # example config: providers + custom shell tool
    └── agent_tools.py       # CLI wrapper ZeroClaw can shell out to
```

## Step-by-step

### 1. Setup

```bash
./setup.sh
```

Pulls `gemma4:4b` and `gemma4:1b`, installs Python deps, and (optionally) installs ZeroClaw.

### 2. Decide on your frontier model

clawhive uses a frontier model for planning. Pick one:

```bash
export ANTHROPIC_API_KEY=sk-ant-...        # Claude (default)
# or
export OPENAI_API_KEY=sk-...               # GPT
# or, if you have no API key:
export CLAWHIVE_PLANNER_LOCAL=1            # use gemma4:12b as the "frontier" surrogate
```

The `CLAWHIVE_PLANNER_LOCAL` mode is the fallback for teams without API access — useful at the hackathon, but the demo is more interesting with a real frontier model so you can see the quality gap.

### 3. Run the orchestrator directly

```bash
python orchestrator.py "Build a Python script that downloads the top 10 HN stories and prints them as markdown."
```

You'll see the plan, each step's implementation, the critic's verdict, and any retry loops:

```
[planner    @ claude-sonnet-4-5  ] 4 steps planned
  1. Fetch HN top stories endpoint
  2. Filter to the top 10 by score
  3. Render as markdown
  4. Print to stdout

[coder      @ gemma4:4b          ] step 1: implementing fetch...
[critic     @ gemma4:1b          ] step 1: PASS
[coder      @ gemma4:4b          ] step 2: implementing filter...
[critic     @ gemma4:1b          ] step 2: FAIL — uses .sort() but doesn't reverse
[coder      @ gemma4:4b          ] step 2: retry...
[critic     @ gemma4:1b          ] step 2: PASS
...
```

### 4. Add the chat surface (ZeroClaw)

Once the orchestrator works on its own, wire it into ZeroClaw to get a chat interface, daemon mode, and Discord/Telegram/webhook channels for free:

```bash
cat zeroclaw/README.md   # five-minute integration guide
```

The integration is the simplest possible thing: ZeroClaw gets a custom shell tool that invokes `python -m clawhive.orchestrator`. The model in the conductor seat is whatever you want — small, big, frontier, fine-tuned.

### 5. Measure the cost/quality trade-off

The point of multi-agent systems with mixed-tier models is *spending frontier tokens only where they matter*. Run the orchestrator with three configurations:

```bash
# all-local: planner is gemma4:12b
CLAWHIVE_PLANNER_LOCAL=1 python orchestrator.py --benchmark

# mixed (default): planner is Claude, workers are local
python orchestrator.py --benchmark

# all-frontier: every role is Claude
CLAWHIVE_ALL_FRONTIER=1 python orchestrator.py --benchmark
```

The benchmark mode runs a fixed eval suite and reports task success rate, total wall-clock time, and frontier API cost (estimated from token counts).

## Suggested challenges

1. **Pareto Frontier of Multi-Agent Cost** — Sweep across role assignments (planner=local/frontier × coder=local/frontier × critic=local/frontier × etc.). Plot quality vs. cost. Find the sweet spot.
2. **Specialist Agents** — Replace the generic `coder` with specialists (sql_coder, test_writer, refactorer). Show that small specialists beat one big generalist on multi-step tasks.
3. **The Critic Question** — Is `gemma4:1b` actually a useful critic, or is it just adding latency? Build an eval that measures critic precision/recall against ground truth. If 1B is too small, what about a distilled 500M from `shrinkray`?
4. **Memory & Long-Running Conversations** — ZeroClaw has a memory store. Wire the orchestrator to remember prior plans and re-use partial solutions.
5. **Multi-Channel Demo** — Deploy ZeroClaw as a daemon on a $5/month VPS. Hook up Discord and a webhook. Demo the same swarm responding to messages from both.
6. **Adversarial Critic** — Replace the critic with a "red team" agent that tries to break the coder's output. Compare retry rates.
7. **Speculative Frontier Calls** — Run the planner on local Gemma 4 12B and Claude in parallel. Use the local one's plan if it agrees with Claude's; otherwise only pay for Claude. Measure cost reduction at fixed quality.

## Why this is the hardest track

Multi-agent systems are easy to write and very hard to make work. You will run into:

- **Disagreement loops** — planner says one thing, coder does another, critic flags it, planner doesn't update. Bound your loops.
- **Context drift** — by step 5, the coder has lost track of step 1. You'll need a memory strategy.
- **Cost explosions** — every retry is more frontier tokens. Cap retries; have the critic provide structured feedback so retries are bounded.
- **The "where to put the smarts" question** — if you put Claude in the planner only, the workers may be too dumb to execute the plan. If you put it in the coder, the planner produces incoherent specs.

These are real production problems that bigger orgs spend quarters on. A weekend gets you a meaningful demo.
