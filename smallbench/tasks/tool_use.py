"""Tool-calling reliability tasks. The grader checks the model called the right tool with valid args."""
import json


def make_grader(expected_tool: str, required_keys: list[str], key_checks: dict | None = None):
    """Returns a grader that requires a specific tool call with required keys.

    key_checks is an optional dict of key -> expected substring (case-insensitive).
    """
    def grader(resp) -> tuple[bool, str]:
        tcs = resp.tool_calls or []
        if not tcs:
            return False, "no tool call made"
        if tcs[0].function.name != expected_tool:
            return False, f"called {tcs[0].function.name}, expected {expected_tool}"
        try:
            args = json.loads(tcs[0].function.arguments)
        except json.JSONDecodeError as e:
            return False, f"args not valid JSON: {e}"
        for k in required_keys:
            if k not in args:
                return False, f"missing required arg: {k}"
        if key_checks:
            for k, needle in key_checks.items():
                if needle.lower() not in str(args.get(k, "")).lower():
                    return False, f"arg {k}={args.get(k)!r} should contain {needle!r}"
        return True, "ok"

    return grader


WEATHER_TOOL = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Look up current weather for a city.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name"},
                "units": {"type": "string", "enum": ["celsius", "fahrenheit"]},
            },
            "required": ["city"],
        },
    },
}

EMAIL_TOOL = {
    "type": "function",
    "function": {
        "name": "send_email",
        "description": "Send an email.",
        "parameters": {
            "type": "object",
            "properties": {
                "to": {"type": "string"},
                "subject": {"type": "string"},
                "body": {"type": "string"},
            },
            "required": ["to", "subject", "body"],
        },
    },
}


TASKS = [
    {
        "id": "weather_simple",
        "prompt": "What's the weather in Tokyo right now?",
        "tools": [WEATHER_TOOL],
        "grader": make_grader("get_weather", ["city"], {"city": "Tokyo"}),
    },
    {
        "id": "email_compose",
        "prompt": (
            "Send an email to alice@example.com with subject 'Lunch?' and a short "
            "body suggesting Thursday at noon."
        ),
        "tools": [EMAIL_TOOL],
        "grader": make_grader(
            "send_email",
            ["to", "subject", "body"],
            {"to": "alice@example.com", "subject": "Lunch"},
        ),
    },
    {
        "id": "no_tool_needed",
        "prompt": "What is 2 + 2? Answer directly without using any tools.",
        "tools": [WEATHER_TOOL, EMAIL_TOOL],
        "grader": lambda resp: (
            (not resp.tool_calls and "4" in (resp.content or "")),
            "ok" if (not resp.tool_calls and "4" in (resp.content or "")) else "called a tool unnecessarily or wrong answer",
        ),
    },
]
