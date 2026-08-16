"""Build a fingerprinted embedding cache from a caller-supplied CSV."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer


def fingerprint(frame: pd.DataFrame, id_column: str, text_column: str) -> str:
    digest = hashlib.sha256()
    for row in frame[[id_column, text_column]].itertuples(index=False):
        digest.update(str(row[0]).encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(row[1]).encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-stem", type=Path, required=True)
    parser.add_argument("--id-column", default="document_id")
    parser.add_argument("--text-column", default="text")
    parser.add_argument("--embedding-model", default="all-MiniLM-L6-v2")
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    frame = pd.read_csv(args.input)
    required = {args.id_column, args.text_column}
    missing = required.difference(frame.columns)
    if missing:
        raise SystemExit(f"missing columns: {', '.join(sorted(missing))}")
    frame = frame.dropna(subset=[args.text_column]).reset_index(drop=True)

    vectors_path = args.output_stem.with_suffix(".npz")
    metadata_path = args.output_stem.with_suffix(".json")
    if not args.force and (vectors_path.exists() or metadata_path.exists()):
        raise SystemExit("output exists; pass --force to replace the cache")
    vectors_path.parent.mkdir(parents=True, exist_ok=True)

    model = SentenceTransformer(args.embedding_model)
    vectors = model.encode(
        frame[args.text_column].astype(str).tolist(),
        show_progress_bar=True,
        batch_size=args.batch_size,
    )
    metadata = {
        "embedding_model": args.embedding_model,
        "rows": len(frame),
        "fingerprint": fingerprint(frame, args.id_column, args.text_column),
    }
    np.savez_compressed(vectors_path, embeddings=np.asarray(vectors, dtype="float32"))
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(f"saved {len(frame)} embeddings and fingerprint metadata")


if __name__ == "__main__":
    main()
