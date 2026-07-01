from __future__ import annotations

from pathlib import Path

from scripts.validate_manifest import main
from texttovoz.manifest import ChunkRecord, text_hash


def write_valid_manifest(path: Path) -> None:
    record = ChunkRecord(
        chunk_id=1,
        text="Hola mundo.",
        text_hash=text_hash("Hola mundo."),
        audio_path="chunks/chunk_001.wav",
        duration_s=1.0,
        sample_rate=24_000,
        channels=1,
        status="success",
    )
    path.write_text(record.model_dump_json() + "\n", encoding="utf-8")


def test_manifest_validator_accepts_positional_path(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.jsonl"
    write_valid_manifest(manifest_path)

    assert main([str(manifest_path)]) == 0


def test_manifest_validator_accepts_path_alias(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.jsonl"
    write_valid_manifest(manifest_path)

    assert main(["--path", str(manifest_path)]) == 0


def test_manifest_validator_requires_a_path(capsys) -> None:
    try:
        main([])
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("missing path should exit non-zero")

    assert "manifest path is required" in capsys.readouterr().err
