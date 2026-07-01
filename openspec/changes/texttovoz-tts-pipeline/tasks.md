# Tasks: TextTovoz TTS Pipeline

<!-- Remediation 2026-07-01: no new tasks; fixed verify CRITICAL #1/#2 and quick WARNING #3/#5 surfaces without changing tickboxes. -->

## 1. Scaffolding

- [x] 1.1 [small, ~8 LOC] Create `src/texttovoz/__init__.py` exposing `__version__` and re-exporting `IngestError` after task 2.2.
- [x] 1.2 [small, ~4 LOC] Create `tests/__init__.py` and `scripts/__init__.py` as empty package markers.
- [x] 1.3 [small, ~20 LOC] Create `src/texttovoz/data/acronyms.yaml` with default glossary entries for `ASP.NET`, `API`, `HTTP`, `URL`, `ID`, and `JPG`.

## 2. Pure-Python modules (testable)

- [x] 2.1 [small, ~75 LOC] Implement `src/texttovoz/config.py` with `TTSConfig` dataclass and design defaults for paths, model, audio, seed, and generation parameters.
- [x] 2.2 [small, ~55 LOC] Implement `src/texttovoz/ingest.py` with `load_text(path) -> str` and `IngestError` for missing file, non-UTF-8, and empty content; depends on 2.1.
- [x] 2.3 [medium, ~120 LOC] Implement `src/texttovoz/normalize.py` with PyYAML glossary loading, longest-match acronym expansion, whitespace collapse, and Spanish punctuation preservation; depends on 1.3.
- [x] 2.4 [medium, ~85 LOC] Implement `src/texttovoz/tokenize.py` with lazy spaCy `es_core_news_sm` loading and regex fallback `split_sentences(text) -> list[str]`; depends on 2.3.
- [x] 2.5 [medium, ~120 LOC] Implement `src/texttovoz/chunk.py` with sentence grouping, max-char cap, clause-boundary splitting for oversized sentences, and hard-split fallback; after 2.4.
- [x] 2.6 [medium, ~180 LOC] Implement `src/texttovoz/manifest.py` with Pydantic v2 `ChunkRecord`, append-only newline-safe `ManifestWriter`, keyed `ManifestReader`, fsync writes, and atomic status update helper.
- [x] 2.7 [medium, ~125 LOC] Implement `src/texttovoz/audio_io.py` with `save_wav`, `load_wav`, and `concat_with_silence` using SoundFile plus NumPy/Torch-compatible tensors; after 2.1.

## 3. TTS wrapper

- [x] 3.1 [medium, ~135 LOC] Implement `src/texttovoz/tts.py` with lazy Chatterbox imports, `is_available()`, `ChatterboxTTS.from_pretrained(...)`, and `generate(...)`; no import-time heavy dependency.
- [x] 3.2 [small, ~35 LOC] Add `StubTTS` in `src/texttovoz/tts.py` returning one second of silence for tests when Chatterbox is unavailable; after 3.1.
- [x] 3.3 [large, ~190 LOC] Implement `src/texttovoz/pipeline.py` orchestration for ingest, glossary, normalize, tokenize, chunk, TTS/stub selection, resume, per-chunk errors, manifest upsert, WAV save, final concat/export, and logging; depends on 2.1-2.7 and 3.2.
- [x] 3.4 [small, ~30 LOC] Document resume and `from_chunk`/`to_chunk` slice semantics in `pipeline.py` docstrings; after 3.3.

## 4. Tests

- [x] 4.1 [small, ~60 LOC] Add `tests/conftest.py` fixtures for temp input/output dirs, tiny Spanish text, glossary, stub config, and sample tensors.
- [x] 4.2 [medium, ~95 LOC] Add `tests/test_normalize.py` covering acronym expansion, longest-match behavior, whitespace, accents, `¿¡`, and punctuation-only edge cases; after 2.3.
- [x] 4.3 [medium, ~85 LOC] Add `tests/test_tokenize.py` covering spaCy path via monkeypatch and regex fallback on Spanish fixtures; after 2.4.
- [x] 4.4 [medium, ~100 LOC] Add `tests/test_chunk.py` covering caps, sentence-boundary preservation, clause splitting, and hard-split fallback; after 2.5.
- [x] 4.5 [medium, ~120 LOC] Add `tests/test_manifest.py` covering `ChunkRecord` schema, append-only JSONL, newline guarantee, keyed reads, and atomic status update; after 2.6.
- [x] 4.6 [medium, ~85 LOC] Add `tests/test_audio_io.py` covering WAV round-trip and silence-gap concat length; after 2.7.
- [x] 4.7 [large, ~130 LOC] Add `tests/test_pipeline_smoke.py` for full stubbed run, manifest success rows, skipped resume, and final concat length; after 3.3.

## 5. Tooling

- [x] 5.1 [small, ~70 LOC] Create `pyproject.toml` with project metadata, test extras, Ruff `E,F,I,B,UP`, line length 100, py310 target, format defaults, and pytest testpaths.
- [x] 5.2 [small, ~25 LOC] Create pinned `requirements.txt` matching design dependency notes, keeping local verification CPU-safe and Colab heavy installs explicit.
- [x] 5.3 [small, ~85 LOC] Create `scripts/validate_manifest.py` argparse CLI validating JSONL rows through `ChunkRecord` and exiting non-zero on schema errors; depends on 2.6.

## 6. Notebook UX

- [x] 6.1 [medium, ~260 LOC] Create `notebooks/tts_pipeline.ipynb` with install/check, HF cache pre-warm, config, dry-run preview, full tqdm run, export, and `display(Audio(...))` cells calling package APIs only; after 3.3 and 5.1.

## 7. Docs

- [x] 7.1 [small, ~80 LOC] Update `README.md` with quickstart, personal-use-only / AI-generated audio disclaimer, Colab notes, and link to `AGENTS.md`; after 6.1.
- [x] 7.2 [small, ~25 LOC] Update `AGENTS.md` with verification commands: Ruff, pytest, smoke test, and `python scripts/validate_manifest.py output/manifest.jsonl`; after 5.3.

## Review Workload Forecast

- **Estimated changed lines**: ~2,120
- **Number of new files**: 23
- **Estimated tasks**: 25
- **Tasks per file (avg/max)**: 1.1/4
- **Chained PRs recommended**: Yes
- **400-line budget risk**: High
- **Decision needed before apply**: Yes
- **Chain strategy**: pending
- **Reasoning**: This change creates a package, notebook, tests, tooling, and docs; tests and notebook JSON alone likely exceed the 400-line review budget. Suggested slices are: foundation modules/tests, TTS+pipeline smoke, tooling/docs/notebook. With `single-pr-default`, the orchestrator should get approval for chained PRs or a size exception before apply.

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: pending
400-line budget risk: High
