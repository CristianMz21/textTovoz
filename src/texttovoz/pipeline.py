"""Pipeline orchestration for TextTovoz.

Resume semantics are manifest-driven: chunks with an existing manifest row whose
``status`` is ``success`` and whose ``text_hash`` matches the planned chunk text
are skipped. Rows with ``pending`` or ``error`` are eligible for regeneration.

Slice semantics use inclusive 1-based chunk IDs. ``TTSConfig.from_chunk`` limits
the first eligible chunk, and ``TTSConfig.to_chunk`` limits the last eligible
chunk. Chunks outside the slice are left untouched and excluded from this run's
generation loop.

Final WAV export is all-or-nothing for the selected window: the pipeline writes
``output/full.wav`` only when at least one selected chunk succeeded and no
selected chunk failed in the current run.
"""

from __future__ import annotations

import importlib
import logging
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

from texttovoz.audio_io import concat_with_silence, load_wav, save_wav
from texttovoz.chunk import chunk_sentences
from texttovoz.config import TTSConfig
from texttovoz.ingest import load_text
from texttovoz.manifest import ChunkRecord, ManifestReader, text_hash
from texttovoz.normalize import load_glossary, normalize
from texttovoz.tokenize import split_sentences
from texttovoz.tts import ChatterboxTTS, StubTTS, is_available

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class RunResult:
    """Summary of one pipeline run."""

    chunks_total: int
    chunks_selected: int
    generated: int
    skipped: int
    errors: int
    manifest_path: Path
    output_wav_path: Path


def run(config: TTSConfig) -> RunResult:
    """Run ingest, preprocessing, TTS generation, manifesting, and export."""

    LOGGER.info("Starting TextTovoz pipeline")
    config.chunks_dir.mkdir(parents=True, exist_ok=True)
    config.output_dir.mkdir(parents=True, exist_ok=True)

    text = load_text(config.input_path)
    glossary = load_glossary(config.glossary_path)
    normalized = normalize(text, glossary)
    sentences = split_sentences(normalized, max_chars=config.max_chars)
    chunks = chunk_sentences(sentences, max_chars=config.max_chars)
    planned = _planned_records(chunks, config)
    _check_manifest_collision(
        config.manifest_path,
        planned,
        refuse=config.refuse_manifest_collision,
    )

    selected = [record for record in planned if _within_slice(record.chunk_id, config)]
    existing = ManifestReader(config.manifest_path).by_chunk_id()
    tts = _load_tts(config)

    records_by_id = {record.chunk_id: existing.get(record.chunk_id, record) for record in planned}
    generated = 0
    skipped = 0
    errors = 0

    for record in selected:
        existing_record = existing.get(record.chunk_id)
        if _can_skip(existing_record, record):
            skipped += 1
            LOGGER.info("Skipping successful chunk %s", record.chunk_id)
            continue

        try:
            _seed_for_chunk(config.seed + record.chunk_id)
            wav_path = config.chunks_dir / f"chunk_{record.chunk_id:03d}.wav"
            audio, sample_rate = tts.generate(record.text)
            save_wav(wav_path, audio, sample_rate=sample_rate)
            saved_audio, saved_rate = load_wav(wav_path)
            duration_s = len(saved_audio) / saved_rate if saved_rate else 0.0
            records_by_id[record.chunk_id] = record.model_copy(
                update={
                    "audio_path": str(wav_path),
                    "duration_s": duration_s,
                    "sample_rate": saved_rate,
                    "channels": config.channels,
                    "status": "success",
                    "generated_at": datetime.now(UTC),
                    "error": None,
                }
            )
            generated += 1
            LOGGER.info("Generated chunk %s", record.chunk_id)
        except Exception as exc:
            errors += 1
            LOGGER.exception("Chunk %s failed", record.chunk_id)
            records_by_id[record.chunk_id] = record.model_copy(
                update={
                    "status": "error",
                    "generated_at": datetime.now(UTC),
                    "error": str(exc),
                }
            )

        _write_manifest(
            config.manifest_path,
            [records_by_id[index] for index in sorted(records_by_id)],
        )

    if not selected:
        _write_manifest(
            config.manifest_path,
            [records_by_id[index] for index in sorted(records_by_id)],
        )

    successful_paths = [
        Path(records_by_id[record.chunk_id].audio_path)
        for record in selected
        if records_by_id[record.chunk_id].status == "success"
    ]
    if successful_paths and errors == 0:
        concat_with_silence(
            successful_paths,
            config.output_wav_path,
            sample_rate=config.sample_rate,
            silence_ms=config.silence_gap_ms,
        )

    return RunResult(
        chunks_total=len(chunks),
        chunks_selected=len(selected),
        generated=generated,
        skipped=skipped,
        errors=errors,
        manifest_path=config.manifest_path,
        output_wav_path=config.output_wav_path,
    )


def _load_tts(config: TTSConfig) -> ChatterboxTTS | StubTTS:
    if is_available():
        LOGGER.info("Loading Chatterbox TTS")
        return ChatterboxTTS.from_pretrained(
            config.model_id,
            config.language_id,
            "cuda",
            config=config,
        )
    LOGGER.warning("Chatterbox unavailable; using StubTTS")
    return StubTTS(config)


def _planned_records(chunks: list[str], config: TTSConfig) -> list[ChunkRecord]:
    return [
        ChunkRecord(
            chunk_id=index,
            text=chunk,
            text_hash=text_hash(chunk),
            audio_path=str(config.chunks_dir / f"chunk_{index:03d}.wav"),
            watermark_present=config.watermark_present,
            language_id=config.language_id,
            model_id=config.model_id,
            exaggeration=config.exaggeration,
            cfg_weight=config.cfg_weight,
            temperature=config.temperature,
            seed=config.seed + index,
            status="pending",
        )
        for index, chunk in enumerate(chunks, start=1)
    ]


def _can_skip(existing: ChunkRecord | None, planned: ChunkRecord) -> bool:
    return (
        existing is not None
        and existing.status == "success"
        and existing.text_hash == planned.text_hash
        and Path(existing.audio_path).exists()
    )


def _within_slice(chunk_id: int, config: TTSConfig) -> bool:
    if config.from_chunk is not None and chunk_id < config.from_chunk:
        return False
    if config.to_chunk is not None and chunk_id > config.to_chunk:
        return False
    return True


def _check_manifest_collision(
    path: Path,
    planned: list[ChunkRecord],
    *,
    refuse: bool,
) -> None:
    if not refuse or not path.exists():
        return
    planned_by_id = {record.chunk_id: record for record in planned}
    for existing in ManifestReader(path).records():
        planned_record = planned_by_id.get(existing.chunk_id)
        if planned_record is None or planned_record.text_hash != existing.text_hash:
            raise ValueError(
                "Manifest collision detected for a different run; remove the manifest "
                "or set refuse_manifest_collision=False"
            )


def _seed_for_chunk(seed: int) -> None:
    try:
        torch = importlib.import_module("torch")
    except ImportError:
        return
    torch.manual_seed(seed)


def _write_manifest(path: Path, records: list[ChunkRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        temp_name = handle.name
        for record in records:
            handle.write(record.model_dump_json())
            handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    Path(temp_name).replace(path)
