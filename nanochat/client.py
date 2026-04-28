"""Unified client for local Ollama (Gemma 4) and Ollama Cloud (Nemotron-3 Nano).

Same call signature for both. Set NANOCHAT_USE_NEMOTRON=1 + OLLAMA_API_KEY to swap.
"""
import os
from ollama import Client


LOCAL_MODEL = os.environ.get("NANOCHAT_LOCAL_MODEL", "gemma4:4b")
CLOUD_MODEL = os.environ.get("NANOCHAT_CLOUD_MODEL", "nemotron-3-nano:30b-cloud")


def make_client() -> tuple[Client, str]:
    """Returns (client, model_tag). Picks local or cloud based on env."""
    if os.environ.get("NANOCHAT_USE_NEMOTRON"):
        api_key = os.environ.get("OLLAMA_API_KEY")
        if not api_key:
            raise RuntimeError(
                "NANOCHAT_USE_NEMOTRON is set but OLLAMA_API_KEY is missing. "
                "Sign up at https://ollama.com/cloud and export OLLAMA_API_KEY."
            )
        client = Client(
            host="https://ollama.com",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        return client, CLOUD_MODEL
    # local
    client = Client(host=os.environ.get("OLLAMA_HOST", "http://localhost:11434"))
    return client, LOCAL_MODEL


def stream_chat(client: Client, model: str, messages: list, **opts):
    """Yields content chunks. Wraps Ollama's streaming chat into a clean iterator."""
    stream = client.chat(model=model, messages=messages, stream=True, options=opts or None)
    for chunk in stream:
        msg = chunk.get("message", {})
        if msg.get("content"):
            yield msg["content"]


def chat_blocking(client: Client, model: str, messages: list, **opts) -> str:
    """Non-streaming chat. Used by compare.py for batch evals."""
    resp = client.chat(model=model, messages=messages, options=opts or None)
    return resp["message"]["content"]
