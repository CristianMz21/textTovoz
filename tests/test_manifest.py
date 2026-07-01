from __future__ import annotations

import json

import pytest

from texttovoz.manifest import (
    ChunkRecord,
    ManifestReader,
    ManifestWriter,
    text_hash,
    update_status_atomic,
)


def make_record(chunk_id: int = 1, status: str = "pending") -> ChunkRecord:
    return ChunkRecord(
        chunk_id=chunk_id,
        text=f"Chunk {chunk_id}",
        text_hash=text_hash(f"Chunk {chunk_id}"),
        audio_path=f"chunks/chunk_{chunk_id:03d}.wav",
        status=status,
    )


def test_chunk_record_requires_sha256_hash() -> None:
    with pytest.raises(ValueError):
        ChunkRecord(chunk_id=1, text="x", text_hash="bad", audio_path="x.wav")


def test_manifest_writer_appends_jsonl_with_newline(tmp_path) -> None:
    path = tmp_path / "manifest.jsonl"
    ManifestWriter(path).append(make_record())

    raw = path.read_text(encoding="utf-8")
    assert raw.endswith("\n")
    assert json.loads(raw)["chunk_id"] == 1


def test_manifest_reader_exposes_keyed_records(tmp_path) -> None:
    path = tmp_path / "manifest.jsonl"
    writer = ManifestWriter(path)
    writer.append(make_record(1))
    writer.append(make_record(2, "success"))

    reader = ManifestReader(path)
    assert reader.by_chunk_id()[2].status == "success"
    assert reader.by_text_hash()[text_hash("Chunk 1")].chunk_id == 1


def test_update_status_atomic_rewrites_single_record(tmp_path) -> None:
    path = tmp_path / "manifest.jsonl"
    writer = ManifestWriter(path)
    writer.append(make_record(1))
    writer.append(make_record(2))

    updated = update_status_atomic(path, 2, "error", error="CUDA OOM")

    records = ManifestReader(path).by_chunk_id()
    assert updated.error == "CUDA OOM"
    assert records[1].status == "pending"
    assert records[2].status == "error"
