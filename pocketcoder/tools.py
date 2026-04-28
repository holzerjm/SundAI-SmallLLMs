"""Tool implementations and OpenAI-format schemas for the pocketcoder agent.

Keep this file small. Adding tools makes small models worse, not better.
Start with read_file / write_file / bash / finish; add the rest only when you
hit a wall on a real task.
"""
import json
import subprocess
from pathlib import Path


SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a text file.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string", "description": "Path relative to cwd"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write text to a file, creating parent directories as needed. Overwrites existing content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Replace a unique string in a file with new text. The old_text must appear exactly once.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "old_text": {"type": "string"},
                    "new_text": {"type": "string"},
                },
                "required": ["path", "old_text", "new_text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Run a shell command in the current working directory. 30s timeout.",
            "parameters": {
                "type": "object",
                "properties": {"cmd": {"type": "string"}},
                "required": ["cmd"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_dir",
            "description": "List files and subdirectories in a directory.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string", "default": "."}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "grep",
            "description": "Search for a regex pattern across files. Returns matching lines with paths.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string"},
                    "path": {"type": "string", "default": "."},
                },
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "finish",
            "description": "Call this when the task is complete. Provide a short summary of what was done.",
            "parameters": {
                "type": "object",
                "properties": {"summary": {"type": "string"}},
                "required": ["summary"],
            },
        },
    },
]


def _read_file(path: str) -> str:
    p = Path(path)
    if not p.exists():
        return f"ERROR: {path} does not exist"
    if p.is_dir():
        return f"ERROR: {path} is a directory; use list_dir"
    text = p.read_text()
    return text if len(text) < 50_000 else text[:50_000] + "\n... [truncated]"


def _write_file(path: str, content: str) -> str:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return f"wrote {len(content)} bytes to {path}"


def _edit_file(path: str, old_text: str, new_text: str) -> str:
    p = Path(path)
    if not p.exists():
        return f"ERROR: {path} does not exist"
    text = p.read_text()
    n = text.count(old_text)
    if n == 0:
        return "ERROR: old_text not found in file"
    if n > 1:
        return f"ERROR: old_text appears {n} times; make it unique"
    p.write_text(text.replace(old_text, new_text))
    return f"edited {path}"


def _bash(cmd: str) -> str:
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        return "ERROR: command timed out after 30s"
    out = f"exit={r.returncode}"
    if r.stdout:
        out += f"\nstdout:\n{r.stdout[:5000]}"
    if r.stderr:
        out += f"\nstderr:\n{r.stderr[:5000]}"
    return out


def _list_dir(path: str = ".") -> str:
    p = Path(path)
    if not p.exists():
        return f"ERROR: {path} does not exist"
    items = []
    for item in sorted(p.iterdir()):
        suffix = "/" if item.is_dir() else ""
        items.append(f"{item.name}{suffix}")
    return "\n".join(items) if items else "(empty)"


def _grep(pattern: str, path: str = ".") -> str:
    try:
        r = subprocess.run(
            ["grep", "-rn", "--exclude-dir=.git", "--exclude-dir=node_modules",
             "--exclude-dir=__pycache__", pattern, path],
            capture_output=True, text=True, timeout=10,
        )
    except subprocess.TimeoutExpired:
        return "ERROR: grep timed out"
    return r.stdout[:5000] if r.stdout else "(no matches)"


def execute(name: str, args: dict) -> str:
    """Dispatch a tool call by name. Returns a string for the model to read."""
    try:
        if name == "read_file":
            return _read_file(args["path"])
        if name == "write_file":
            return _write_file(args["path"], args["content"])
        if name == "edit_file":
            return _edit_file(args["path"], args["old_text"], args["new_text"])
        if name == "bash":
            return _bash(args["cmd"])
        if name == "list_dir":
            return _list_dir(args.get("path", "."))
        if name == "grep":
            return _grep(args["pattern"], args.get("path", "."))
        if name == "finish":
            return f"FINISH: {args.get('summary', '')}"
        return f"ERROR: unknown tool {name}"
    except KeyError as e:
        return f"ERROR: missing required arg {e}"
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"


def parse_args(raw: str) -> dict:
    """Tool args come as JSON strings. Be forgiving — small models sometimes emit slightly broken JSON."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # try one common fix: single -> double quotes
        try:
            return json.loads(raw.replace("'", '"'))
        except json.JSONDecodeError:
            return {}
