"""Client factory. Same OpenAI-compatible interface for local + Anthropic + OpenAI.

Anthropic's SDK is a separate import; we wrap it to match the chat.completions shape so
the rest of the codebase doesn't care whether a call goes to Claude, GPT, or local Gemma.
"""
import os
from dataclasses import dataclass
from openai import OpenAI


LOCAL_BASE = "http://localhost:11434/v1"
ANTHROPIC_BASE = "https://api.anthropic.com/v1"
OPENAI_BASE = "https://api.openai.com/v1"


@dataclass
class ModelSpec:
    """Describes which provider + model to use for a given role."""
    provider: str           # "local" | "anthropic" | "openai"
    model: str              # provider-specific tag
    label: str              # short label for logs (e.g. "claude-sonnet-4-5")


def planner_spec() -> ModelSpec:
    """Pick the planner based on env. Order: explicit override → API keys → local fallback."""
    if os.environ.get("CLAWHIVE_ALL_FRONTIER"):
        return _frontier_spec()
    if os.environ.get("CLAWHIVE_PLANNER_LOCAL"):
        return ModelSpec("local", "gemma4:12b", "gemma4:12b")
    if os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("OPENAI_API_KEY"):
        return _frontier_spec()
    # graceful fallback: local 12b for hackathon teams without API keys
    return ModelSpec("local", "gemma4:12b", "gemma4:12b (no-api-key fallback)")


def coder_spec() -> ModelSpec:
    if os.environ.get("CLAWHIVE_ALL_FRONTIER"):
        return _frontier_spec()
    return ModelSpec("local", os.environ.get("CLAWHIVE_CODER", "gemma4:4b"),
                     os.environ.get("CLAWHIVE_CODER", "gemma4:4b"))


def critic_spec() -> ModelSpec:
    if os.environ.get("CLAWHIVE_ALL_FRONTIER"):
        return _frontier_spec()
    return ModelSpec("local", os.environ.get("CLAWHIVE_CRITIC", "gemma4:1b"),
                     os.environ.get("CLAWHIVE_CRITIC", "gemma4:1b"))


def _frontier_spec() -> ModelSpec:
    if os.environ.get("ANTHROPIC_API_KEY"):
        return ModelSpec("anthropic", "claude-sonnet-4-5", "claude-sonnet-4-5")
    if os.environ.get("OPENAI_API_KEY"):
        return ModelSpec("openai", "gpt-4o", "gpt-4o")
    raise RuntimeError("no frontier API key — set ANTHROPIC_API_KEY or OPENAI_API_KEY, "
                       "or set CLAWHIVE_PLANNER_LOCAL=1 for the local fallback.")


def chat(spec: ModelSpec, messages: list, **kw) -> tuple[str, dict]:
    """Run a chat completion and return (content, usage_dict).

    usage_dict has {input_tokens, output_tokens} so the orchestrator can estimate cost.
    """
    if spec.provider == "anthropic":
        # convert OpenAI-style messages to Anthropic shape
        return _chat_anthropic(spec, messages, **kw)
    if spec.provider == "openai":
        client = OpenAI(base_url=OPENAI_BASE, api_key=os.environ["OPENAI_API_KEY"])
    else:  # local
        client = OpenAI(base_url=os.environ.get("OPENAI_BASE_URL", LOCAL_BASE),
                        api_key=os.environ.get("OPENAI_API_KEY", "not-needed"))
    resp = client.chat.completions.create(model=spec.model, messages=messages, **kw)
    usage = {
        "input_tokens": resp.usage.prompt_tokens if resp.usage else 0,
        "output_tokens": resp.usage.completion_tokens if resp.usage else 0,
    }
    return resp.choices[0].message.content or "", usage


def _chat_anthropic(spec: ModelSpec, messages: list, **kw) -> tuple[str, dict]:
    from anthropic import Anthropic
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    # Anthropic separates system messages from the messages array
    system_msgs = [m["content"] for m in messages if m["role"] == "system"]
    other_msgs = [m for m in messages if m["role"] != "system"]
    resp = client.messages.create(
        model=spec.model,
        system="\n\n".join(system_msgs) if system_msgs else "You are a helpful assistant.",
        messages=other_msgs,
        max_tokens=kw.get("max_tokens", 4096),
    )
    content = "".join(block.text for block in resp.content if hasattr(block, "text"))
    usage = {"input_tokens": resp.usage.input_tokens, "output_tokens": resp.usage.output_tokens}
    return content, usage


# rough $/1M token rates for the cost estimator. update as needed.
PRICING = {
    "claude-sonnet-4-5": {"input": 3.00, "output": 15.00},
    "gpt-4o":            {"input": 2.50, "output": 10.00},
}


def estimate_cost(spec: ModelSpec, usage: dict) -> float:
    """Returns estimated USD cost. Local models are $0."""
    p = PRICING.get(spec.model)
    if not p:
        return 0.0
    return (usage["input_tokens"] * p["input"] + usage["output_tokens"] * p["output"]) / 1_000_000
