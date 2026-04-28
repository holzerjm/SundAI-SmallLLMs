"""Interactive REPL. Type messages, the agent uses tools, conversation persists."""
from client import make_client, MODEL
from prompts import SYSTEM
import tools as T


def main():
    client = make_client()
    msgs = [{"role": "system", "content": SYSTEM}]
    print(f"pocketcoder ready. model: {MODEL}. ctrl-d to exit.\n")

    while True:
        try:
            user = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user:
            continue
        msgs.append({"role": "user", "content": user})

        # let the model run tools until it stops calling them
        for _ in range(20):
            resp = client.chat.completions.create(
                model=MODEL, messages=msgs, tools=T.SCHEMAS,
            ).choices[0].message
            msgs.append(resp.model_dump(exclude_none=True))

            if not resp.tool_calls:
                print(resp.content or "(no content)")
                break

            for tc in resp.tool_calls:
                args = T.parse_args(tc.function.arguments)
                result = T.execute(tc.function.name, args)
                short = result[:200].replace("\n", " ")
                print(f"  [{tc.function.name}] {str(args)[:80]} -> {short}")
                msgs.append({"role": "tool", "tool_call_id": tc.id, "content": result})
                if tc.function.name == "finish":
                    print(f"(finished: {args.get('summary', '')})")
                    break
            else:
                continue
            break


if __name__ == "__main__":
    main()
