# Wiring clawhive into ZeroClaw

This is the optional chat-surface integration. The Python orchestrator already works on its own (`python orchestrator.py "..."`). [ZeroClaw](https://github.com/zeroclaw-labs/zeroclaw) gives you a polished chat agent on top: CLI, Discord/Telegram/Matrix/email channels, daemon mode, and a memory store — without writing any Rust.

## How the integration works

ZeroClaw runs a single conductor agent. We give that conductor one custom tool: `delegate_to_swarm`. When a user asks the conductor for something complex, the conductor decides whether to answer directly (chitchat, simple lookups) or delegate to the swarm (anything that benefits from Plan → Act → Critique).

```
user message
   ↓
ZeroClaw conductor (gemma4:4b, the chat model)
   ↓ (decides to delegate)
delegate_to_swarm tool → shells out → python -m clawhive.agent_tools delegate "..."
   ↓
clawhive Python orchestrator (planner=Claude, coder=gemma4:4b, critic=gemma4:1b)
   ↓
result returned to ZeroClaw → user
```

The conductor model is intentionally small (gemma4:4b). Its job is *triage*, not heavy reasoning. The frontier tokens are spent inside the swarm, only when actually needed.

## Five-minute integration

### 1. Install ZeroClaw

```bash
cargo install zeroclaw
# or download a prebuilt binary:
# https://github.com/zeroclaw-labs/zeroclaw/releases
```

### 2. Drop the config

```bash
mkdir -p ~/.zeroclaw
cp zeroclaw.toml ~/.zeroclaw/config.toml
```

The config registers two model providers (Ollama + Anthropic) and one custom shell tool that calls our Python entry point.

### 3. Make the entry point executable

```bash
# from the clawhive/ directory:
chmod +x zeroclaw/agent_tools.py
```

### 4. Talk to it

```bash
zeroclaw agent
```

```
> hi
hello! what can i help you with?

> what's 2 + 2?
4.

> build me a python script that fetches the top 10 hn stories as markdown
[delegate_to_swarm] task: "build me a python script that fetches..."
[planner    @ claude-sonnet-4-5  ] 4 steps planned
[coder      @ gemma4:4b          ] step 1: implementing fetch...
... (full swarm trace) ...

here's the assembled script:
```python
...
```
```

The conductor knows when to delegate based on the system prompt (`conductor_prompt.md`).

### 5. (Optional) deploy as a daemon with Discord/Telegram

ZeroClaw's docs cover this. The relevant config sections in `zeroclaw.toml` are commented out — uncomment, fill in your bot tokens, and `zeroclaw service install`.

## What the integration is NOT doing

This is the simplest possible wiring: ZeroClaw as a chat skin over a Python orchestrator. There's no Rust code, no MCP server, no custom crate.

For a more advanced integration you could:

- **Re-implement the swarm in Rust** as a native ZeroClaw crate (the "right" way, but it's a hackathon — start simple).
- **Make each specialist its own MCP server** so any MCP-compatible host (Claude Code, Claude Desktop, Continue, etc.) can use the same swarm.
- **Use ZeroClaw's "Standard Operating Procedures"** (cron, MQTT, webhooks) to trigger the swarm on events — e.g., a webhook from GitHub fires the swarm to triage a new issue.

## Files in this directory

- `zeroclaw.toml` — drop into `~/.zeroclaw/config.toml`
- `agent_tools.py` — Python CLI that ZeroClaw shells out to
- `conductor_prompt.md` — the conductor's system prompt (what makes it triage vs. delegate)
