"""Transcript ingestion helpers."""

from __future__ import annotations

from pathlib import Path


class IngestError(ValueError):
    """Raised when transcript input cannot be used for TTS."""


def load_text(path: str | Path) -> str:
    """Load a non-empty UTF-8 transcript from *path*."""

    input_path = Path(path)
    if not input_path.exists():
        raise IngestError(f"Input file is missing: {input_path}")
    if not input_path.is_file():
        raise IngestError(f"Input path is not a file: {input_path}")
    try:
        text = input_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise IngestError(f"Input file is not valid UTF-8: {input_path}") from exc
    if not text.strip():
        raise IngestError(f"Input file has no usable text: {input_path}")
    return text
