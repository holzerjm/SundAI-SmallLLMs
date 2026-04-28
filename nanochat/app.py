"""Streamlit chat UI. Run with:
  streamlit run app.py -- --corpus corpus.json
"""
import argparse
import os
import sys

import streamlit as st

from chat import answer
from retrieval import load


def parse_argv():
    """Streamlit eats argv. Anything after `--` is for us."""
    argv = sys.argv[1:]
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="corpus.json")
    return ap.parse_args(argv)


def main():
    args = parse_argv()

    st.set_page_config(page_title="nanochat", layout="wide")
    st.title("nanochat — corpus-grounded Q&A")

    # show the active model & mode in the sidebar
    with st.sidebar:
        if os.environ.get("NANOCHAT_USE_NEMOTRON"):
            st.success("model: nemotron-3-nano:30b-cloud")
        else:
            model = os.environ.get("NANOCHAT_LOCAL_MODEL", "gemma4:4b")
            st.info(f"model: {model} (local)")

        mode = st.radio("retrieval mode", ["smart", "all"], horizontal=True)
        corpus_path = st.text_input("corpus path", args.corpus)

        try:
            corpus = load(corpus_path)
            st.caption(f"{len(corpus['segments'])} segments, ~{corpus['total_tokens']} tokens")
        except Exception as e:
            st.error(f"corpus load failed: {e}")
            return

        if st.button("clear conversation"):
            st.session_state.messages = []
            st.rerun()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # render history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if user_input := st.chat_input("ask a question..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # bounded history for the model: last 10 turns, excluding current question
        history = st.session_state.messages[:-1][-10:]

        with st.chat_message("assistant"):
            placeholder = st.empty()
            buffer = []
            for chunk in answer(user_input, corpus_path, mode=mode, history=history):
                buffer.append(chunk)
                placeholder.markdown("".join(buffer))
            full = "".join(buffer)
            st.session_state.messages.append({"role": "assistant", "content": full})


if __name__ == "__main__":
    main()
