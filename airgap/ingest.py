"""Walk a directory, chunk text files, embed, save a single JSON index."""
import argparse
import json
from pathlib import Path

from client import make_client, embed


TEXT_EXTS = {".md", ".txt", ".rst", ".py", ".js", ".ts", ".go", ".java", ".rb", ".html", ".org"}


def chunk(text: str, size: int = 1000, overlap: int = 200) -> list[str]:
    """Naive character-based chunking with overlap. Replace with smarter strategies."""
    chunks = []
    i = 0
    while i < len(text):
        chunks.append(text[i:i + size])
        i += size - overlap
    return chunks


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
    ap.add_argument("--out", default="index.json")
    ap.add_argument("--chunk-size", type=int, default=1000)
    ap.add_argument("--overlap", type=int, default=200)
    args = ap.parse_args()

    root = Path(args.path).resolve()
    files = walk_files(root)
    print(f"found {len(files)} files under {root}")

    records = []
    for f in files:
        try:
            text = f.read_text(errors="ignore")
        except Exception as e:
            print(f"  skip {f}: {e}")
            continue
        for i, c in enumerate(chunk(text, args.chunk_size, args.overlap)):
            records.append({
                "path": str(f.relative_to(root)),
                "chunk_id": i,
                "text": c,
            })

    print(f"chunked into {len(records)} pieces. embedding...")
    client = make_client()
    batch_size = 32
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        vecs = embed(client, [r["text"] for r in batch])
        for r, v in zip(batch, vecs):
            r["embedding"] = v
        print(f"  embedded {min(i + batch_size, len(records))}/{len(records)}")

    Path(args.out).write_text(json.dumps({"root": str(root), "records": records}))
    print(f"\nwrote {args.out} with {len(records)} chunks")


if __name__ == "__main__":
    main()
