"""Chat + embedding clients. Both default to local Ollama."""
import os
from openai import OpenAI


def make_client(base_url: str | None = None) -> OpenAI:
    base_url = base_url or os.environ.get("OPENAI_BASE_URL", "http://localhost:11434/v1")
    api_key = os.environ.get("OPENAI_API_KEY", "not-needed")
    return OpenAI(base_url=base_url, api_key=api_key)


CHAT_MODEL = os.environ.get("AIRGAP_CHAT_MODEL", "gemma4:4b")
EMBED_MODEL = os.environ.get("AIRGAP_EMBED_MODEL", "nomic-embed-text")


def embed(client: OpenAI, texts: list[str]) -> list[list[float]]:
    """Get embeddings for a batch of strings."""
    resp = client.embeddings.create(model=EMBED_MODEL, input=texts)
    return [d.embedding for d in resp.data]


def chat(client: OpenAI, messages: list, **kw) -> str:
    return client.chat.completions.create(model=CHAT_MODEL, messages=messages, **kw).choices[0].message.content
