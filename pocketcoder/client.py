"""Shared OpenAI-compatible client. Set OPENAI_BASE_URL to swap backends."""
import os
from openai import OpenAI


def make_client(base_url: str | None = None) -> OpenAI:
    base_url = base_url or os.environ.get("OPENAI_BASE_URL", "http://localhost:11434/v1")
    api_key = os.environ.get("OPENAI_API_KEY", "not-needed")
    return OpenAI(base_url=base_url, api_key=api_key)


MODEL = os.environ.get("POCKETCODER_MODEL", "qwen3:8b")
