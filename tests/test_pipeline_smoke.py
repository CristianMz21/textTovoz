from __future__ import annotations

from pathlib import Path

from texttovoz import pipeline
from texttovoz.config import TTSConfig
from texttovoz.manifest import ManifestReader


def make_config(tmp_path: Path) -> TTSConfig:
    input_path = tmp_path / "subtitle.txt"
    glossary_path = tmp_path / "acronyms.yaml"
    input_path.write_text(
        "¿Qué es ASP.NET? Es una API para HTTP. ¡Vamos con una URL simple!",
        encoding="utf-8",
    )
    glossary_path.write_text(
        "ASP.NET: A-S-P punto N-E-T\nAPI: A-P-I\nHTTP: H-T-T-P\nURL: U-R-L\n",
        encoding="utf-8",
    )
    return TTSConfig(
        input_path=input_path,
        chunks_dir=tmp_path / "chunks",
        output_dir=tmp_path / "output",
        manifest_path=tmp_path / "chunks" / "manifest.jsonl",
        output_wav_path=tmp_path / "output" / "full.wav",
        glossary_path=glossary_path,
        max_chars=45,
    )


def test_pipeline_stub_run_writes_success_manifest(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(pipeline, "is_available", lambda: False)
    config = make_config(tmp_path)

    result = pipeline.run(config)

    records = ManifestReader(config.manifest_path).records()
    assert result.generated == len(records)
    assert result.errors == 0
    assert {record.status for record in records} == {"success"}
    assert config.output_wav_path.exists()


def test_pipeline_rerun_skips_successful_chunks(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(pipeline, "is_available", lambda: False)
    config = make_config(tmp_path)

    first = pipeline.run(config)
    second = pipeline.run(config)

    assert first.generated > 0
    assert second.generated == 0
    assert second.skipped == first.generated


def test_pipeline_isolates_chunk_errors(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(pipeline, "is_available", lambda: False)
    original_generate = pipeline.StubTTS.generate
    calls = {"count": 0}

    def raise_once(self: pipeline.StubTTS, text: str):
        calls["count"] += 1
        if calls["count"] == 2:
            raise RuntimeError("synthetic chunk failure")
        return original_generate(self, text)

    monkeypatch.setattr(pipeline.StubTTS, "generate", raise_once)
    config = make_config(tmp_path)

    result = pipeline.run(config)

    records = ManifestReader(config.manifest_path).records()
    statuses = [record.status for record in records]
    assert result.errors == 1
    assert "error" in statuses
    assert statuses.count("success") == len(records) - 1
    assert records[1].error == "synthetic chunk failure"
    assert not config.output_wav_path.exists()
