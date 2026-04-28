"""Structured-output tasks. Grader parses JSON from the response and checks fields."""
import json
import re


def parse_json(text: str) -> dict | None:
    """Find the first {...} block in the text and try to parse it."""
    fence = re.search(r"```(?:json)?\s*\n(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        try:
            return json.loads(fence.group(1))
        except json.JSONDecodeError:
            pass
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            return None
    return None


def make_grader(checks: dict):
    """checks is field -> expected value (or callable taking actual -> bool)."""
    def grader(resp) -> tuple[bool, str]:
        data = parse_json(resp.content or "")
        if data is None:
            return False, "no valid JSON found"
        for field, expected in checks.items():
            actual = data.get(field)
            ok = expected(actual) if callable(expected) else actual == expected
            if not ok:
                return False, f"{field}={actual!r}, expected {expected!r}"
        return True, "ok"

    return grader


TASKS = [
    {
        "id": "person",
        "prompt": (
            "Extract the person's info from this text and return ONLY a JSON object "
            'with keys "name", "age", "city":\n\n'
            "Hi, I'm Ada Lovelace, I'm 36 and I live in London."
        ),
        "grader": make_grader({
            "name": lambda v: v and "Ada" in str(v) and "Lovelace" in str(v),
            "age": 36,
            "city": "London",
        }),
    },
    {
        "id": "invoice",
        "prompt": (
            'Extract invoice fields as JSON with keys "invoice_id", "total_usd", "due_date":\n\n'
            "Invoice #INV-2024-0042 — Total: $1,247.50 — Due 2024-12-15. Thanks!"
        ),
        "grader": make_grader({
            "invoice_id": lambda v: v and "INV-2024-0042" in str(v),
            "total_usd": lambda v: float(str(v).replace("$", "").replace(",", "")) == 1247.50,
            "due_date": lambda v: v and "2024-12-15" in str(v),
        }),
    },
    {
        "id": "list_extraction",
        "prompt": (
            'List the programming languages mentioned, as JSON: {"languages": [...]}.\n\n'
            "I started with BASIC, moved to Python, dabbled in Rust, and recently picked up Zig."
        ),
        "grader": make_grader({
            "languages": lambda v: isinstance(v, list) and {"BASIC", "Python", "Rust", "Zig"}.issubset(set(v)),
        }),
    },
]
