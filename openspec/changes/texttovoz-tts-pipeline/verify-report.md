# Verify Report: texttovoz-tts-pipeline

**Status**: OK
**Change**: `texttovoz-tts-pipeline`
**Version**: N/A
**Mode**: Standard verify
**Artifact store**: OpenSpec file
**Verified at**: 2026-07-01

All requested quality gates pass, all 25 tasks are complete, and the three previously identified CRITICAL issues are resolved. The documented manifest validation command now targets `chunks/manifest.jsonl` in both `README.md` and `AGENTS.md`; because the pipeline has not yet run, the command exits non-zero with the expected clear missing-manifest message rather than an argparse/path mismatch.

## Completeness

| Metric | Value |
|---|---:|
| Tasks total | 25 |
| Tasks marked complete | 25 |
| Tasks incomplete | 0 |
| Requirements total | 16 |
| Requirements PASS | 10 |
| Requirements PARTIAL | 6 |
| Requirements MISSING | 0 |

## Build & Tests Execution

Commands were run in the requested order.

### `ruff check .`

**Result**: PASS

```text
All checks passed!
```

### `ruff format --check .`

**Result**: PASS

```text
24 files already formatted
```

### `python3 -m pytest -q`

**Result**: PASS

```text
............................                                             [100%]
28 passed in 0.60s
```

### `python3 -m pytest -q tests/test_pipeline_smoke.py`

**Result**: PASS

```text
...                                                                      [100%]
3 passed in 0.56s
```

### `python scripts/validate_manifest.py --help`

**Result**: PASS

```text
usage: validate_manifest.py [-h] [--path PATH_ALIAS] [--strict] [path]

Validate a TextTovoz manifest JSONL file.

positional arguments:
  path               Path to chunks/manifest.jsonl

options:
  -h, --help         show this help message and exit
  --path PATH_ALIAS  Path to chunks/manifest.jsonl
  --strict           Reject blank lines, duplicate chunk IDs, and empty
                     manifests.
```

### Documented docs/path gate

**Result**: PASS

Evidence:

```text
README.md:51: python scripts/validate_manifest.py chunks/manifest.jsonl
AGENTS.md:49: python scripts/validate_manifest.py chunks/manifest.jsonl
No README.md or AGENTS.md matches for output/manifest.jsonl.
```

Documented command behavior:

```bash
python scripts/validate_manifest.py chunks/manifest.jsonl
```

```text
error: Manifest not found: chunks/manifest.jsonl

EXIT_CODE=1
```

This is acceptable for the current repository state because no pipeline run has produced `chunks/manifest.jsonl`. The validator does not produce an argparse error, and the exit semantics are correct for a missing required artifact.

## Coverage Evidence

Command:

```bash
python3 -m pytest -q --cov=src/texttovoz --cov-report=term-missing
```

Output:

```text
............................                                             [100%]
================================ tests coverage ================================
_______________ coverage: platform linux, python 3.14.6-final-0 ________________

Name                         Stmts   Miss  Cover   Missing
----------------------------------------------------------
src/texttovoz/__init__.py        4      0   100%
src/texttovoz/audio_io.py       45     11    76%   37, 43, 56, 58, 60, 64, 67-71
src/texttovoz/chunk.py          67      6    91%   19, 25, 42, 64, 74-75
src/texttovoz/config.py         45      7    84%   41, 43, 45, 47, 49, 51, 57
src/texttovoz/ingest.py         16      5    69%   17, 19, 22-23, 25
src/texttovoz/manifest.py       86      3    97%   99, 101, 105
src/texttovoz/normalize.py      35      4    89%   21, 23, 27, 51
src/texttovoz/pipeline.py      111      7    94%   124, 155-156, 197, 199, 215, 226
src/texttovoz/tokenize.py       40      3    92%   18, 28, 36
src/texttovoz/tts.py            27      1    96%   35
----------------------------------------------------------
TOTAL                          476     47    90%
28 passed in 0.76s
```

Coverage sanity: total remains 90%. Below-90 modules are still `audio_io.py` 76%, `config.py` 84%, `ingest.py` 69%, and `normalize.py` 89%.

## Static Checks Beyond Ruff

### Forbidden suppressions

Command:

```bash
grep -RIn "noqa\|type: ignore\|pylint: disable\|nosec\|pytest\.mark\.skip\|pytest\.mark\.skipif\|coverage: ignore\|coverage: no-cover\|unittest\.skip" src tests scripts notebooks
```

**Result**: PASS

```text
(no output)
```

### Notebook nbformat / JSON validation

Command:

```bash
python3 - <<'PY'
import json
nb=json.load(open('notebooks/tts_pipeline.ipynb', encoding='utf-8'))
print('notebook JSON OK')
print(len(nb.get('cells', [])))
print(nb.get('nbformat'), nb.get('nbformat_minor'))
PY
```

**Result**: PASS

```text
notebook JSON OK
10
4 5
```

### Config defaults

**Result**: PASS

`TTSConfig()` still has `max_chars=280`, `sample_rate=24000`, `channels=1`, `silence_gap_ms=100`, `language_id="es"`, `model_id="ResembleAI/Chatterbox-Multilingual-es-mx-latam"`, `hf_home=/content/.cache/huggingface`, `watermark_present=True`, and `manifest_path=chunks/manifest.jsonl`.

### Manifest schema

**Result**: PASS

`ChunkRecord` contains the design-required fields plus `seed`: `chunk_id`, `text`, `text_hash`, `audio_path`, `duration_s`, `sample_rate`, `channels`, `watermark_present`, `language_id`, `model_id`, `exaggeration`, `cfg_weight`, `temperature`, `seed`, `status`, `generated_at`, and `error`.

## Specific Critical Re-checks

### CRITICAL #1 — positional manifest validator and docs

**Remediation status**: RESOLVED.

- `scripts/validate_manifest.py:44-50` defines an optional positional `path` and a backwards-compatible `--path` alias.
- `tests/test_validate_manifest.py:23-45` pins positional path, `--path` alias, and missing-path parser behavior.
- Runtime evidence: `python scripts/validate_manifest.py --help` shows `positional arguments: path`.
- Runtime evidence: `python scripts/validate_manifest.py chunks/manifest.jsonl` exits `1` with `error: Manifest not found: chunks/manifest.jsonl`, which is correct because no pipeline run has produced the manifest yet.

### CRITICAL #2 — Chatterbox `model_id` forwarding

**Remediation status**: RESOLVED.

- `src/texttovoz/tts.py:49-67` accepts `model_id` and calls `ChatterboxMultilingualTTS.from_pretrained(model_id, device=device)`.
- `src/texttovoz/pipeline.py:153-161` passes `config.model_id`, `config.language_id`, and `config=config` into the wrapper.
- `tests/test_tts_stub.py:17-46` monkeypatches a fake Chatterbox module and asserts `calls["model_id"] == "ResembleAI/Chatterbox-Multilingual-es-mx-latam"`, `device == "cuda"`, and `language_id == "es"`.
- Runtime evidence: full test suite passed with 28 tests.

### CRITICAL #3 — docs/path mismatch

**Remediation status**: RESOLVED.

- `README.md:44-52` documents `python scripts/validate_manifest.py chunks/manifest.jsonl`.
- `AGENTS.md:42-50` documents `python scripts/validate_manifest.py chunks/manifest.jsonl`.
- Search evidence found no `output/manifest.jsonl` string in `README.md` or `AGENTS.md`.
- Runtime evidence: the documented command now targets the canonical pipeline manifest path and fails only with `error: Manifest not found: chunks/manifest.jsonl` because no pipeline output exists yet.

## Spec Compliance Matrix

| Requirement | Status | File:line evidence | Runtime/test evidence | Notes |
|---|---|---|---|---|
| SK-SPEC-001 Input Ingest | PARTIAL | `src/texttovoz/ingest.py:12-26`; `tests/test_pipeline_smoke.py:10-42` | Full pytest passed | Valid ingest is exercised through smoke; missing/non-UTF-8/empty errors are implemented but still not directly tested. |
| SK-SPEC-002 Text Normalization | PASS | `src/texttovoz/normalize.py:15-56`; `src/texttovoz/data/acronyms.yaml:1-6` | `tests/test_normalize.py` passed | Covers glossary loading, longest-match expansion, whitespace/control trimming, Spanish punctuation, and punctuation-only exclusion. |
| SK-SPEC-003 Sentence Tokenization | PASS | `src/texttovoz/tokenize.py:14-59` | `tests/test_tokenize.py` passed | Covers regex fallback, monkeypatched spaCy path, and long sentence cap splitting. |
| SK-SPEC-004 Chunking | PASS | `src/texttovoz/chunk.py:15-87` | `tests/test_chunk.py` passed | Covers cap enforcement, grouping, clause splitting, and hard split fallback. |
| SK-SPEC-005 TTS Generation | PASS | `src/texttovoz/tts.py:49-82`; `src/texttovoz/pipeline.py:153-161` | `tests/test_tts_stub.py:17-46`; `tests/test_pipeline_smoke.py` passed | Stub path and wrapper semantics are tested; real Chatterbox generation remains unrun locally by heavy dependency/GPU constraints, but configured model-id forwarding is pinned. |
| SK-SPEC-006 Watermarking | PASS | `src/texttovoz/config.py:33,46-47`; `src/texttovoz/manifest.py:28`; `src/texttovoz/pipeline.py:173` | Smoke manifest tests passed | Watermark declaration defaults true and config rejects disabling it. |
| SK-SPEC-007 Manifest Emission | PARTIAL | `src/texttovoz/manifest.py:16-37,40-75`; `src/texttovoz/pipeline.py:166-183`; `scripts/validate_manifest.py:13-71` | `tests/test_manifest.py`; `tests/test_validate_manifest.py`; docs gate passed | Schema/persistence and validator positional/alias behavior are implemented and tested. Manifest path collision refusal is implemented in `pipeline.py:203-218` but not directly tested. |
| SK-SPEC-008 Resume and Slice Regeneration | PARTIAL | `src/texttovoz/pipeline.py:3-10,71-83,195-200`; `src/texttovoz/config.py:36-37,48-57` | Rerun skip smoke test passed | Resume skip is tested; inclusive `from_chunk`/`to_chunk` semantics are implemented but still not directly tested. |
| SK-SPEC-009 Output Export | PASS | `src/texttovoz/audio_io.py:27-51`; `src/texttovoz/pipeline.py:129-140` | `tests/test_audio_io.py`; `tests/test_pipeline_smoke.py:32-42,57-79` passed | Concatenates WAVs with 100 ms silence and suppresses final WAV when selected chunks fail. |
| SK-SPEC-010 Preview | PASS | `notebooks/tts_pipeline.ipynb:143-166` | Notebook JSON validation passed | Notebook statically contains two-chunk preview and inline `IPython.display.Audio`; not executed locally because it is Colab/GPU-oriented. |
| SK-SPEC-011 Disclaimer and Personal Use | PASS | `notebooks/tts_pipeline.ipynb:8-10,214-216`; `README.md:14-19` | Static/document inspection | Personal-use-only and AI-generated-audio notices are visible. |
| SK-SPEC-012 Reproducibility | PARTIAL | `src/texttovoz/config.py:26`; `src/texttovoz/pipeline.py:88,179,221-226`; `src/texttovoz/tts.py:9-10` | No golden-byte reproducibility test | Seed is recorded and applied when `torch` is importable, but identical output bytes are not proven by tests. |
| SK-SPEC-013 Failure Isolation | PASS | `src/texttovoz/pipeline.py:87-121` | `tests/test_pipeline_smoke.py:57-79` passed | One chunk error is recorded and later chunks are still attempted. |
| SK-SPEC-014 Colab Fit and Cold Start | PARTIAL | `notebooks/tts_pipeline.ipynb:36-80`; `src/texttovoz/config.py:19`; `requirements.txt:1-5` | Notebook JSON validation passed | HF cache path and install/prewarm cells exist; real Colab cold-start/GPU fit was not run, and local requirements intentionally omit heavy Chatterbox/spaCy dependencies. |
| SK-SPEC-015 Idempotent Rerun | PASS | `src/texttovoz/pipeline.py:3-10,80-85,186-192` | `tests/test_pipeline_smoke.py:45-54` passed | Rerun skips successful chunks with matching hash and existing audio. |
| SK-SPEC-016 Consent Gate Deferred Hook | PARTIAL | `proposal.md:16-18`; `design.md:106,130` | No code/test evidence | MVP excludes cloning, but no explicit future consent-gate hook exists in config/notebook/source. |

**Compliance summary**: 10/16 PASS, 6/16 PARTIAL, 0/16 MISSING.

## Coherence (Design)

| Design item | Followed? | Evidence | Notes |
|---|---|---|---|
| Package under `src/texttovoz/` with thin notebook UX | Yes | `src/texttovoz/*`, `notebooks/tts_pipeline.ipynb` | Implemented. |
| Spanish tokenizer: spaCy plus fallback | Partial | `src/texttovoz/tokenize.py`; `tests/test_tokenize.py` | Code supports spaCy if installed; local verified path is regex fallback plus monkeypatched spaCy. |
| Editable acronym glossary | Yes | `src/texttovoz/data/acronyms.yaml`; `normalize.py` | Implemented. |
| WAV concat via NumPy/SoundFile | Yes | `src/texttovoz/audio_io.py` | Implemented and tested. |
| Resume by status + matching hash | Yes | `src/texttovoz/pipeline.py:80-85,186-192` | Tested. |
| HF cache `/content/.cache/huggingface` | Yes | `config.py:19`; notebook cache cell | Implemented. |
| Seed control `seed + chunk_id` | Partial | `pipeline.py:88,179,221-226` | Implemented but reproducible bytes are untested. |
| Failure isolation | Yes | `pipeline.py:87-121`; smoke test | Tested. |
| Slice regeneration | Partial | `config.py:36-37`; `pipeline.py:195-200` | Implemented but not directly tested. |
| Target LatAm checkpoint | Yes | `config.py:20`; `tts.py:49-67`; `test_tts_stub.py:17-46` | The prior mismatch is resolved. |
| Verify commands in project docs | Yes | `README.md:51`; `AGENTS.md:49`; docs gate | Project docs now use `chunks/manifest.jsonl` and no longer mention `output/manifest.jsonl`. |

## Task Tickbox Audit Summary

All 25 tasks in `tasks.md` are checked. No checked task is completely missing from the working tree.

| Task group | Status | Evidence | Notes |
|---|---|---|---|
| 1. Scaffolding | PASS | `src/texttovoz/__init__.py`; `tests/__init__.py`; `scripts/__init__.py`; `acronyms.yaml` | Implemented. |
| 2. Pure-Python modules | PASS | `config.py`, `ingest.py`, `normalize.py`, `tokenize.py`, `chunk.py`, `manifest.py`, `audio_io.py` | Implemented; coverage warnings remain for some modules. |
| 3. TTS wrapper | PASS | `tts.py:49-82`; `pipeline.py:153-161`; `tests/test_tts_stub.py:17-46` | Stub and model-id forwarding behavior are tested. |
| 4. Tests | PASS | `tests/test_*.py` | 28 tests pass; some scenarios remain untested. |
| 5. Tooling | PASS | `pyproject.toml`; `requirements.txt`; `scripts/validate_manifest.py`; docs command probe | Validator CLI is fixed and the documented path behavior is now correct. |
| 6. Notebook UX | PASS | `notebooks/tts_pipeline.ipynb` | Valid nbformat 4, 10 cells. |
| 7. Docs | PASS | `README.md:44-52`; `AGENTS.md:42-50` | Docs are consistent with each other and with the default manifest path. |

## Issues Found

### CRITICAL

None.

### WARNING

1. **Coverage target is still missed for several modules.** Below 90%: `audio_io.py` 76%, `config.py` 84%, `ingest.py` 69%, and `normalize.py` 89%. Total coverage is 90%.
2. **Some required scenarios remain untested.** Missing direct tests include ingest rejection, manifest collision refusal, slice regeneration, reproducible bytes, Colab cold-start/GPU fit, and future consent hook behavior.
3. **spaCy design remains optional in verified implementation.** `tokenize.py` can use spaCy if present, but local requirements/notebook verification do not prove `es_core_news_sm` installation or real runtime behavior beyond monkeypatching.
4. **Consent gate deferred hook is not represented in code.** MVP excludes cloning, but SK-SPEC-016 asks for a future blocking hook if cloning is later enabled.

### SUGGESTION

1. Add focused tests for `TTSConfig` validation branches, `audio_io` tensor/stereo/error branches, `ManifestReader`/`update_status_atomic` edge cases, ingest failure paths, manifest collision, and slice regeneration.
2. If spaCy is intended as the primary tokenizer in Colab, make the notebook install/load path explicit; otherwise update design/spec language to make regex fallback the primary verified MVP path.
3. During archive/spec sync, reconcile historical OpenSpec design lines that still mention `output/manifest.jsonl` as an alternative or old exact command, even though README/AGENTS are now corrected.

## Verdict

PASS WITH WARNINGS

Archive can proceed with high confidence: all three prior CRITICALs are resolved, all requested gates pass, and remaining findings are coverage/test-depth/design-follow-up items rather than release blockers for this SDD change.
