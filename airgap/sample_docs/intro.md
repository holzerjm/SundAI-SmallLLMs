# SundAI Small Models Hack — Sample Knowledge Base

This is a small example corpus you can use to test the airgap RAG pipeline before pointing it at your own documents.

## About the hackathon

The Small Models Hack is a SundAI club event focused on the new generation of local language models. Recent releases like Gemma 4 and Qwen 3.6 have made it feasible to run capable models on a laptop, and the goal of the hack is to push these models in real applications — agentic harnesses, on-device assistants, custom fine-tunes — and to build evals that show what they can and can't do.

## Hardware notes

- A 16GB MacBook Air can run Qwen 3.6 8B at usable speeds via MLX or Ollama.
- For 30B-class models, 32GB+ unified memory is recommended.
- Embedding models like nomic-embed-text use about 300MB of RAM.

## What "airgap" means here

The full pipeline — chunking, embedding, retrieval, and generation — runs entirely on your local machine via Ollama. No part of your documents, queries, or the model's responses is sent to any external service. You can verify this by disconnecting your network and confirming the app still works.

## When you'd want this

- Legal teams reviewing privileged documents.
- Medical workflows where patient data cannot leave the device.
- Personal assistants that read your journal, calendar, or finances.
- Internal company knowledge bases on regulated networks.
- Anyone who simply prefers their notes not be training data.
