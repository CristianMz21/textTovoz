"""JSONL manifest schema and persistence helpers."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Status = Literal["pending", "success", "error"]


class ChunkRecord(BaseModel):
    """One chunk generation manifest row."""

    model_config = ConfigDict(extra="forbid")

    chunk_id: int = Field(ge=1)
    text: str = Field(min_length=1)
    text_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    audio_path: str
    duration_s: float | None = Field(default=None, ge=0)
    sample_rate: int | None = Field(default=None, ge=1)
    channels: int | None = Field(default=None, ge=1)
    watermark_present: bool = True
    language_id: str = "es"
    model_id: str = "ResembleAI/Chatterbox-Multilingual-es-mx-latam"
    exaggeration: float = 0.5
    cfg_weight: float = 0.5
    temperature: float = 0.8
    seed: int = 42
    status: Status = "pending"
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    error: str | None = None


class ManifestWriter:
    """Append-only JSONL writer with newline and fsync guarantees."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def append(self, record: ChunkRecord) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = record.model_dump_json()
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(payload)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())


class ManifestReader:
    """Read JSONL manifests and expose keyed chunk records."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def records(self) -> list[ChunkRecord]:
        if not self.path.exists():
            return []
        rows: list[ChunkRecord] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(ChunkRecord.model_validate_json(line))
        return rows

    def by_chunk_id(self) -> dict[int, ChunkRecord]:
        return {record.chunk_id: record for record in self.records()}

    def by_text_hash(self) -> dict[str, ChunkRecord]:
        return {record.text_hash: record for record in self.records()}


def update_status_atomic(
    path: str | Path,
    chunk_id: int,
    status: Status,
    *,
    error: str | None = None,
    audio_path: str | None = None,
    duration_s: float | None = None,
) -> ChunkRecord:
    """Atomically rewrite a manifest with one chunk status updated."""

    manifest_path = Path(path)
    records = ManifestReader(manifest_path).records()
    updated: ChunkRecord | None = None
    new_records: list[ChunkRecord] = []
    for record in records:
        if record.chunk_id != chunk_id:
            new_records.append(record)
            continue
        payload = {"status": status, "error": error, "generated_at": datetime.now(UTC)}
        if audio_path is not None:
            payload["audio_path"] = audio_path
        if duration_s is not None:
            payload["duration_s"] = duration_s
        updated = record.model_copy(update=payload)
        new_records.append(updated)
    if updated is None:
        raise KeyError(f"chunk_id not found in manifest: {chunk_id}")
    _write_records_atomic(manifest_path, new_records)
    return updated


def _write_records_atomic(path: Path, records: list[ChunkRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        temp_name = handle.name
        for record in records:
            handle.write(record.model_dump_json())
            handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    Path(temp_name).replace(path)


def text_hash(text: str) -> str:
    """Return the manifest hash format for chunk text."""

    import hashlib

    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()
