"""Shared OpenAI-compatible client."""
import os
from openai import OpenAI


def make_client(base_url: str | None = None) -> OpenAI:
    base_url = base_url or os.environ.get("OPENAI_BASE_URL", "http://localhost:11434/v1")
    api_key = os.environ.get("OPENAI_API_KEY", "not-needed")
    return OpenAI(base_url=base_url, api_key=api_key)


def chat(client: OpenAI, model: str, messages: list, **kw) -> str:
    return client.chat.completions.create(model=model, messages=messages, **kw).choices[0].message.content or ""
