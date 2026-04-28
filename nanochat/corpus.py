"""Walk a directory, segment text into passages, save a single JSON corpus artifact.

No embeddings. No vector DB. Just text and a token index for fast lexical scoring.
"""
import argparse
import json
import re
from pathlib import Path


TEXT_EXTS = {".md", ".txt", ".rst", ".py", ".js", ".ts", ".go", ".java", ".rb", ".html", ".org"}

# rough token count for budgeting; close enough for retrieval purposes
def approx_tokens(text: str) -> int:
    return max(1, len(text) // 4)


# segment splitting: paragraph-like blocks of roughly target_tokens each
def segment(text: str, target_tokens: int = 200) -> list[str]:
    paragraphs = re.split(r"\n\s*\n", text)
    out, buf, buf_tok = [], [], 0
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        t = approx_tokens(p)
        if buf and buf_tok + t > target_tokens:
            out.append("\n\n".join(buf))
            buf, buf_tok = [p], t
        else:
            buf.append(p)
            buf_tok += t
    if buf:
        out.append("\n\n".join(buf))
    return out


_TOKEN_RE = re.compile(r"[a-zA-Z0-9]+")


def tokenize(text: str) -> list[str]:
    return [w.lower() for w in _TOKEN_RE.findall(text)]


def walk_files(root: Path) -> list[Path]:
    files = []
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in TEXT_EXTS:
            if any(part.startswith(".") for part in p.parts):
                continue
            files.append(p)
    return files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", help="directory to ingest")
    ap.add_argument("--out", default="corpus.json")
    ap.add_argument("--target-tokens", type=int, default=200, help="approx tokens per segment")
    args = ap.parse_args()

    root = Path(args.path).resolve()
    files = walk_files(root)
    print(f"found {len(files)} files under {root}")

    segments = []
    for f in files:
        try:
            text = f.read_text(errors="ignore")
        except Exception as e:
            print(f"  skip {f}: {e}")
            continue
        for i, seg in enumerate(segment(text, args.target_tokens)):
            segments.append({
                "path": str(f.relative_to(root)),
                "segment_id": i,
                "text": seg,
                "tokens": tokenize(seg),
                "approx_tokens": approx_tokens(seg),
            })

    total = sum(s["approx_tokens"] for s in segments)
    Path(args.out).write_text(json.dumps({
        "root": str(root),
        "segments": segments,
        "total_tokens": total,
    }))
    print(f"\nwrote {args.out}: {len(segments)} segments, ~{total} tokens")


if __name__ == "__main__":
    main()
