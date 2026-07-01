"""Validate TextTovoz JSONL manifests."""

from __future__ import annotations

import argparse
from pathlib import Path

from pydantic import ValidationError

from texttovoz.manifest import ChunkRecord


def validate_manifest(path: str | Path, *, strict: bool = False) -> int:
    """Validate a JSONL manifest and return the number of checked rows."""

    manifest_path = Path(path)
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    rows = 0
    seen_chunk_ids: set[int] = set()
    lines = manifest_path.read_text(encoding="utf-8").splitlines()
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            if strict:
                raise ValueError(f"line {line_number}: blank lines are not allowed in strict mode")
            continue
        try:
            record = ChunkRecord.model_validate_json(line)
        except ValidationError as exc:
            raise ValueError(f"line {line_number}: {exc}") from exc
        if strict and record.chunk_id in seen_chunk_ids:
            raise ValueError(f"line {line_number}: duplicate chunk_id {record.chunk_id}")
        seen_chunk_ids.add(record.chunk_id)
        rows += 1
    if strict and rows == 0:
        raise ValueError("manifest is empty")
    return rows


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""

    parser = argparse.ArgumentParser(description="Validate a TextTovoz manifest JSONL file.")
    parser.add_argument("path", nargs="?", type=Path, help="Path to chunks/manifest.jsonl")
    parser.add_argument(
        "--path",
        dest="path_alias",
        type=Path,
        help="Path to chunks/manifest.jsonl",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Reject blank lines, duplicate chunk IDs, and empty manifests.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""

    parser = build_parser()
    args = parser.parse_args(argv)
    manifest_path = args.path if args.path is not None else args.path_alias
    if manifest_path is None:
        parser.error("manifest path is required: pass PATH or --path PATH")
    try:
        validate_manifest(manifest_path, strict=args.strict)
    except (FileNotFoundError, ValueError) as exc:
        parser.exit(1, f"error: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
