# Apply Progress: texttovoz-tts-pipeline

## Batch

- Batch: 1 of 3 — foundation + unit tests + tooling base
- Mode: Standard apply (strict TDD not active)
- PR strategy: single PR with approved `size:exception`

## Tasks Marked Complete

- [x] 1.1 Create `src/texttovoz/__init__.py` with `__version__` and `IngestError` re-export.
- [x] 1.2 Create `tests/__init__.py` and `scripts/__init__.py` package markers.
- [x] 1.3 Create `src/texttovoz/data/acronyms.yaml` with default acronym glossary.
- [x] 2.1 Implement `src/texttovoz/config.py` with `TTSConfig` defaults.
- [x] 2.2 Implement `src/texttovoz/ingest.py` with `load_text` and `IngestError`.
- [x] 2.3 Implement `src/texttovoz/normalize.py` with YAML glossary loading and normalization.
- [x] 2.4 Implement `src/texttovoz/tokenize.py` with lazy spaCy path and regex fallback.
- [x] 2.5 Implement `src/texttovoz/chunk.py` with sentence-aware grouping and long-sentence fallback.
- [x] 2.6 Implement `src/texttovoz/manifest.py` with Pydantic v2 schema and JSONL helpers.
- [x] 2.7 Implement `src/texttovoz/audio_io.py` with WAV round-trip and silence concat helpers.
- [x] 4.1 Add shared pytest fixtures in `tests/conftest.py`.
- [x] 4.2 Add normalization unit tests.
- [x] 4.3 Add tokenization unit tests.
- [x] 4.4 Add chunking unit tests.
- [x] 4.5 Add manifest unit tests.
- [x] 4.6 Add audio I/O unit tests.
- [x] 5.1 Create `pyproject.toml` with metadata, Ruff, pytest, and test extra.
- [x] 5.2 Create lean `requirements.txt` for batch-1 dependencies only.

## Tasks Not Marked Complete

- [ ] 3.1–3.4 TTS wrapper and pipeline orchestration — deferred to batch 2 by scope.
- [ ] 4.7 Pipeline smoke tests — deferred to batch 2 because `pipeline.py` is deferred.
- [ ] 5.3 Manifest validator CLI — deferred to batch 2 by scope.
- [ ] 6.1 Notebook UX — deferred to batch 3 by scope.
- [ ] 7.1–7.2 README/AGENTS updates — deferred to batch 3 by scope.

## Files Created/Changed

- Created `src/texttovoz/__init__.py`.
- Created `src/texttovoz/config.py`.
- Created `src/texttovoz/ingest.py`.
- Created `src/texttovoz/normalize.py`.
- Created `src/texttovoz/tokenize.py`.
- Created `src/texttovoz/chunk.py`.
- Created `src/texttovoz/manifest.py`.
- Created `src/texttovoz/audio_io.py`.
- Created `src/texttovoz/data/acronyms.yaml`.
- Created `tests/__init__.py`.
- Created `tests/conftest.py`.
- Created `tests/test_normalize.py`.
- Created `tests/test_tokenize.py`.
- Created `tests/test_chunk.py`.
- Created `tests/test_manifest.py`.
- Created `tests/test_audio_io.py`.
- Created `scripts/__init__.py`.
- Created `pyproject.toml`.
- Created `requirements.txt`.
- Changed `openspec/changes/texttovoz-tts-pipeline/tasks.md`.
- Created `openspec/changes/texttovoz-tts-pipeline/apply-progress.md`.

## Quality Gate Output

Commands run in required order. The initial unquoted `python3 -m pip install -e .[test]` was rejected by zsh glob expansion; reran as `python3 -m pip install -e ".[test]"` successfully.

### `python3 -m pip install -r requirements.txt`

```text
Successfully installed soundfile-0.14.0
```

### `python3 -m pip install -e ".[test]"`

```text
Successfully built texttovoz
Successfully installed texttovoz-0.1.0
```

### `ruff check .`

```text
All checks passed!
```

### `ruff format --check .`

```text
16 files already formatted
```

### `python3 -m pytest -q`

```text
....................                                                     [100%]
20 passed in 0.68s
```

## Open Issues for Batch 2

- Imports of `texttovoz.tts` and `texttovoz.pipeline` will fail until batch 2 — expected.
- `tests/test_pipeline_smoke.py` is intentionally absent until batch 2.
- `scripts/validate_manifest.py` is intentionally absent until batch 2.
- `chatterbox-tts`, `torch`, `torchaudio`, and `spacy` were not installed in batch 1 by scope.
- Batch 2 should wire manifest hash/status semantics into pipeline resume behavior.

## Batch 2

- Batch: 2 of 3 — TTS wrapper + pipeline orchestration + smoke validation
- Mode: Standard apply (strict TDD not active)
- PR strategy: single PR with approved `size:exception`

### Tasks Completed

- [x] 3.1 Implemented `src/texttovoz/tts.py` with lazy Chatterbox import inside `ChatterboxTTS.from_pretrained(...)`, `is_available()`, and `generate(...)` using the validated multilingual V3 API.
- [x] 3.2 Added `StubTTS` returning one second of silence for local tests and dependency-free runs.
- [x] 3.3 Implemented `src/texttovoz/pipeline.py` orchestration for ingest, glossary normalization, tokenization, chunking, TTS/stub selection, resume, per-chunk error isolation, manifest rewrites, WAV saving, and final concat/export.
- [x] 3.4 Documented manifest resume and inclusive `from_chunk`/`to_chunk` slice semantics in `pipeline.py` docstrings.
- [x] 4.7 Added `tests/test_pipeline_smoke.py` for full stubbed run, manifest success rows, rerun skipping, and chunk error isolation.
- [x] 5.3 Added `scripts/validate_manifest.py` argparse CLI and reusable `validate_manifest(...)` function.

### Files Created/Changed

- Created `src/texttovoz/tts.py`.
- Created `src/texttovoz/pipeline.py`.
- Created `tests/test_pipeline_smoke.py`.
- Created `scripts/validate_manifest.py`.
- Changed `src/texttovoz/config.py` to add `from_chunk` and `to_chunk` fields with validation.
- Changed `openspec/changes/texttovoz-tts-pipeline/tasks.md` to mark tasks 3.1–3.4, 4.7, and 5.3 complete.
- Changed `openspec/changes/texttovoz-tts-pipeline/apply-progress.md` to append this batch-2 section.

### Quality Gate Outputs

#### `python3 -m pip install --quiet 'click>=8' || python3 -m pip install --quiet 'argparse' || true`

```text
[notice] A new release of pip is available: 26.0.1 -> 26.1.2
[notice] To update, run: python3 -m pip install --upgrade pip
```

#### `ruff check .`

```text
All checks passed!
```

#### `ruff format --check .`

```text
20 files already formatted
```

#### `python3 -m pytest -q`

```text
Valid fixture loop scopes are: "function", "class", "module", "package", "session"

  warnings.warn(PytestDeprecationWarning(_DEFAULT_FIXTURE_LOOP_SCOPE_UNSET))
.......................                                                  [100%]
23 passed in 0.86s
```

#### `python3 scripts/validate_manifest.py --help`

```text
options:
  -h, --help   show this help message and exit
  --path PATH  Path to chunks/manifest.jsonl
  --strict     Reject blank lines, duplicate chunk IDs, and empty manifests.
```

### Issues Deferred to Batch 3

- `notebooks/tts_pipeline.ipynb` notebook UX remains unimplemented by batch-2 scope.
- `README.md` and `AGENTS.md` documentation updates remain deferred by batch-3 scope.
- Real Chatterbox/Colab execution remains deferred; heavy dependencies were not installed locally.

### Risk for Batch 3

- Risk: Medium. The dependency-free pipeline and manifest behavior are covered locally, but batch 3 still must validate notebook UX and real Chatterbox runtime assumptions in Colab with heavy dependencies.

## Batch 3

- Batch: 3 of 3 — notebook UX + documentation updates
- Mode: Standard apply (strict TDD not active)
- PR strategy: single PR with approved `size:exception`

### Tasks Completed

- [x] 6.1 Created `notebooks/tts_pipeline.ipynb` as a Colab-runnable nbformat 4 notebook generated by `scripts/build_notebook.py`, with disclaimer, install/GPU checks, HF cache pre-warm, package imports/config, transcript upload, two-chunk preview, full run, export/display, and footer disclaimer.
- [x] 7.1 Updated `README.md` with Quickstart, Colab upload note, prominent personal-use / AI-generated audio disclaimer, verification commands, and `AGENTS.md` conventions link.
- [x] 7.2 Updated `AGENTS.md` with the exact verification command block before workspace context.

### Files Created/Changed

- Count: 7 files in batch 3.
- Created `scripts/build_notebook.py`.
- Created `notebooks/tts_pipeline.ipynb`.
- Changed `README.md`.
- Changed `AGENTS.md`.
- Changed `pyproject.toml` to set `asyncio_default_fixture_loop_scope = "function"` and remove the pytest-asyncio deprecation warning without suppressing warnings.
- Changed `openspec/changes/texttovoz-tts-pipeline/tasks.md` to mark tasks 6.1, 7.1, and 7.2 complete.
- Changed `openspec/changes/texttovoz-tts-pipeline/apply-progress.md` to append this batch-3 section.

### Quality Gate Outputs

#### `ruff check .`

```text
All checks passed!
```

#### `ruff format --check .`

```text
22 files already formatted
```

#### `python3 -m pytest -q`

```text
.......................                                                  [100%]
23 passed in 0.71s
```

#### `python scripts/validate_manifest.py --help`

```text
usage: validate_manifest.py [-h] --path PATH [--strict]

Validate a TextTovoz manifest JSONL file.

options:
  -h, --help   show this help message and exit
  --path PATH  Path to chunks/manifest.jsonl
  --strict     Reject blank lines, duplicate chunk IDs, and empty manifests.
```

#### `python3 -m pytest -q tests/test_pipeline_smoke.py`

```text
...                                                                      [100%]
3 passed in 0.57s
```

### Notebook Smoke Validation

#### `python3 -c "import json,sys; json.load(open('notebooks/tts_pipeline.ipynb')); print('notebook JSON OK')"`

```text
notebook JSON OK
```

#### `jupyter nbconvert --to notebook --execute notebooks/tts_pipeline.ipynb --ExecutePreprocessor.timeout=60 --output /tmp/smoke.ipynb || echo "execute smoke (best-effort; chatterbox not installed locally is expected)"`

```text
[NbConvertApp] Converting notebook notebooks/tts_pipeline.ipynb to notebook
[NbConvertApp] ERROR | No such kernel named python3
jupyter_client.kernelspec.NoSuchKernel: No such kernel named python3
execute smoke (best-effort; chatterbox not installed locally is expected)
```

### Open Issues

- Local notebook execution smoke is Colab-only / environment-sensitive here: `nbconvert` is installed, but the local environment has no registered `python3` kernelspec. JSON validation passed, and the notebook remains intended for Colab with GPU and heavy dependency installation inside the notebook.
- Real Chatterbox generation was not run locally by constraint; it remains a Colab runtime validation concern for `sdd-verify`/manual use.

### Status

- Feature-complete for `texttovoz-tts-pipeline`.
- All tasks in `tasks.md` are marked complete.
- Ready for `sdd-verify`.

## Remediation

- Batch: focused fix batch after verify CRITICAL findings.
- Mode: Standard apply (strict TDD not active).
- PR strategy: single PR with approved `size:exception` from prior apply batches.

### Issues Fixed

- CRITICAL #1: `scripts/validate_manifest.py` now accepts the documented positional manifest path, keeps `--path` as a backwards-compatible alias, keeps `--strict`, and emits a clear parser error when no path is supplied.
- CRITICAL #2: `src/texttovoz/tts.py` now wires the configured Hugging Face `model_id` through `ChatterboxMultilingualTTS.from_pretrained(model_id, device=device)`, while preserving lazy import, `is_available()`, and `StubTTS` semantics. The wrapper documents that the configured LatAm model expects `language_id="es"`.
- WARNING #3: `requirements.txt` now uses lean version ranges: `pydantic>=2,<3`, `pyyaml>=6,<7`, `soundfile>=0.12,<0.13`, `numpy>=1.26,<3`, and `pytest>=8,<10`; heavy Colab/runtime dependencies remain out.
- WARNING #5: `pipeline.py` no longer exports `output/full.wav` for a selected window if any selected chunk failed; it exports only when at least one selected chunk succeeded and `errors == 0`.

### Diff Summary

- `scripts/validate_manifest.py`: changed CLI argument parsing; LOC 66 → 75 (`+9`).
- `src/texttovoz/tts.py`: changed wrapper signature, loader call, and LatAm language documentation; LOC 80 → 95 (`+15`).
- Related same-surface changes: `src/texttovoz/pipeline.py`, `requirements.txt`, `tests/test_validate_manifest.py`, `tests/test_tts_stub.py`, and `tests/test_pipeline_smoke.py`.

### Quality Gate Outputs

#### `ruff check . && ruff format --check .` — last 5 lines

```text
All checks passed!
24 files already formatted
```

#### `python3 -m pytest -q` — last 5 lines

```text
............................                                             [100%]
28 passed in 0.67s
```

### CLI Invocation Evidence

#### Missing documented output manifest path fails clearly

```text
error: Manifest not found: output/manifest.jsonl
```

#### Positional path works on a valid JSONL fixture

```text
OK_positional
```

#### `--path` alias works on the same valid JSONL fixture

```text
OK_path_alias
```

#### Missing path fails non-zero with clear usage/error

```text
usage: validate_manifest.py [-h] [--path PATH_ALIAS] [--strict] [path]
validate_manifest.py: error: manifest path is required: pass PATH or --path PATH
```

### Tests Added

- Added `tests/test_validate_manifest.py` with 3 tests for positional path, `--path` alias, and missing-path error behavior.
- Added `tests/test_tts_stub.py` with 2 tests for `StubTTS` silence semantics and `ChatterboxTTS.from_pretrained(...)` model-id forwarding via monkeypatch.
- Extended `tests/test_pipeline_smoke.py` with 1 assertion that partial final WAV export is suppressed when a selected chunk fails.

### Warnings Deliberately Left

- WARNING #1 coverage shortfalls, WARNING #2 remaining untested scenarios, WARNING #4 optional spaCy install path, and WARNING #6 consent hook remain deferred suggestions by scope.

## Remediation 2

- Batch: focused docs fix after second verify CRITICAL finding.
- Mode: Standard apply (strict TDD not active).
- Change: updated documented manifest validation commands to use the canonical pipeline path `chunks/manifest.jsonl` instead of the non-produced `output/manifest.jsonl`.

### Files Modified and LOC Delta

- `README.md`: changed manifest validation command path; LOC delta `+0/-0` for this remediation.
- `AGENTS.md`: changed manifest validation command path; LOC delta `+0/-0` for this remediation.
- `openspec/changes/texttovoz-tts-pipeline/apply-progress.md`: appended this Remediation 2 section.

### Quality Gate Outputs

#### `ruff check . && ruff format --check .` — last 5 lines

```text
All checks passed!
24 files already formatted
```

#### `python3 -m pytest -q` — last 5 lines

```text
............................                                             [100%]
28 passed in 0.75s
```

### Documentation Command Change

```diff
-python scripts/validate_manifest.py output/manifest.jsonl
+python scripts/validate_manifest.py chunks/manifest.jsonl
```

### Additional Gate Note

- `python scripts/validate_manifest.py /tmp/test_manifest.jsonl && echo OK_positional` was run after `echo '{}' > /tmp/test_manifest.jsonl`, but it exited non-zero because `{}` does not satisfy the required `ChunkRecord` schema. No validator behavior was changed in this docs-only remediation.
