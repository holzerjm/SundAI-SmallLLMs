"""Run a single task end-to-end. Usage: python agent.py 'do the thing'."""
import sys

from client import make_client, MODEL
from prompts import SYSTEM
import tools as T


def run(task: str, max_turns: int = 20, verbose: bool = True) -> dict:
    client = make_client()
    msgs = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": task},
    ]

    for turn in range(max_turns):
        resp = client.chat.completions.create(
            model=MODEL, messages=msgs, tools=T.SCHEMAS,
        ).choices[0].message
        msgs.append(resp.model_dump(exclude_none=True))

        if not resp.tool_calls:
            if verbose:
                print(f"\n[model] {resp.content}")
            return {"status": "no_tool_call", "turns": turn + 1}

        for tc in resp.tool_calls:
            args = T.parse_args(tc.function.arguments)
            result = T.execute(tc.function.name, args)
            if verbose:
                preview = str(args)[:100]
                short = result[:200].replace("\n", " ")
                print(f"[{tc.function.name}] {preview} -> {short}")
            msgs.append({"role": "tool", "tool_call_id": tc.id, "content": result})
            if tc.function.name == "finish":
                return {"status": "finished", "turns": turn + 1, "summary": args.get("summary", "")}

    return {"status": "max_turns", "turns": max_turns}


def main():
    if len(sys.argv) < 2:
        print("usage: python agent.py 'task description'")
        sys.exit(1)
    task = " ".join(sys.argv[1:])
    result = run(task)
    print(f"\n[result] {result}")


if __name__ == "__main__":
    main()
