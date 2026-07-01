# Design: TextTovoz TTS Pipeline

## Technical Approach

Build a Colab-runnable, strongly verified Python package under `src/texttovoz/` with a thin notebook UX in `notebooks/tts_pipeline.ipynb`. Pure preprocessing, manifesting, audio I/O, and orchestration live in modules so they can be tested locally with `pytest`, `ruff`, schema validation, mocked integration tests, and notebook smoke checks. The notebook only installs dependencies, configures paths/model settings, previews audio, runs the pipeline, and displays/exports `output/full.wav`.

## Architecture Decisions

| Decision | Alternatives considered | Trade-offs | Why |
|---|---|---|---|
| Spanish sentence tokenizer: spaCy `es_core_news_sm` plus custom clause fallback | Regex; NLTK Punkt | More install time than regex; better Spanish boundary behavior and testable fixture quality. NLTK is lighter but weaker for project-specific acronyms. | Colab cold-start target is 10 min; spaCy small model is acceptable and safer for `¿?`, acronyms, and long sentences. |
| Acronym glossary in `src/texttovoz/data/acronyms.yaml` | Hard-coded dict; TOML | YAML adds one tiny dependency if not parsed manually; TOML is stdlib in 3.11 only. | Data file is editable without code changes; fallback leaves unknown acronyms unchanged. |
| WAV concatenation via NumPy + SoundFile silence gap | `torchaudio.io` streaming | Less cross-format support, but simpler and deterministic for 24 kHz mono WAV. | MVP exports WAV only; MP3/streaming can be added later behind `audio_io.py`. |
| Resume by manifest `status: success` + matching `text_hash` | Timestamp-only skip; overwrite always | Requires schema and hash checks; prevents stale audio reuse. | Idempotent reruns after Colab disconnects without regenerating successful chunks. |
| HF cache: `HF_HOME=/content/.cache/huggingface` + pre-warm cell | Default cache; Drive cache | VM cache is faster but not durable; Drive can timeout with many files. | Fits Colab free-tier speed; durable outputs are manifest/WAVs, not package cache. |
| Seed control with `torch.manual_seed(seed + chunk_id)` | Single global seed; no seed | Reproducibility is best-effort only because Chatterbox/library ops may be stochastic. | Manifest records seed and settings; golden audio test warns on drift, not fails. |
| Logging via stdlib `logging`, preview via `IPython.display.Audio` | Print-only; rich logging framework | Minimal dependency and works in CLI/tests/notebook. | Keeps notebook readable while modules remain non-notebook-specific. |
| Failure isolation: per-chunk `try/except`, append `status: error`, continue | Abort on first error | Final concat requires all selected chunks success; errors are explicit. | Protects long Colab runs from one OOM/bad chunk. |
| Slice regeneration CLI via `argparse` | Typer | Typer is nicer but extra dependency. | `argparse` is stdlib and enough for `--from-chunk`/`--to-chunk`. |

## Data Flow

```text
subtitle.txt → ingest → normalize → tokenize → chunk → generate(chatterbox)
                                                           │
                                                           ├→ persist chunks/chunk_NNN.wav
                                                           ├→ append chunks/manifest.jsonl
                                                           └→ preview branch: IPython.display.Audio
success WAVs → concat(+100 ms silence) → output/full.wav → display(Audio(...))
```

Notebook cells run install/checks, HF login/cache pre-warm, config, dry-run preview, full `tqdm` run, and export/display. Modules run all business logic for local verification and Colab reuse.

Colab plan: cell 1 installs `chatterbox-tts==0.1.7` and project deps, then errors if Python <3.10 or no CUDA GPU; cell 2 optionally logs into HF and pre-warms `ResembleAI/Chatterbox-Multilingual-es-mx-latam`; cell 3 sets paths/seeds/chunk cap; cell 4 generates one preview chunk; cell 5 runs full generation with `tqdm`; cell 6 exports and displays final WAV. If cold start exceeds 10 min, retry with a fresh runtime, lower dependency extras, or pre-stage model cache where practical.

## File Changes

| File | Action | Description |
|---|---|---|
| `notebooks/tts_pipeline.ipynb` | Create | Thin Colab/Jupyter orchestrator and preview UI. |
| `src/texttovoz/__init__.py` | Create | Package marker/version. |
| `src/texttovoz/pipeline.py` | Create | Orchestrates ingest → normalize → tokenize → chunk → generate → manifest → concat. |
| `src/texttovoz/ingest.py` | Create | UTF-8 loading, missing/empty/non-UTF errors. |
| `src/texttovoz/normalize.py` | Create | Whitespace, edge chars, acronyms, number speech rules. |
| `src/texttovoz/tokenize.py` | Create | spaCy Spanish sentence splitting plus clause fallback. |
| `src/texttovoz/chunk.py` | Create | Sentence-aware grouping, default 280-char cap. |
| `src/texttovoz/tts.py` | Create | Chatterbox load/generate wrapper for HF model. |
| `src/texttovoz/manifest.py` | Create | Pydantic v2 schema, JSONL read/append/validate/resume. |
| `src/texttovoz/audio_io.py` | Create | WAV save/load, mono mixdown, NumPy concat, silence gap. |
| `src/texttovoz/config.py` | Create | Dataclass-style settings and defaults. |
| `src/texttovoz/data/acronyms.yaml` | Create | Default acronym pronunciation glossary. |
| `tests/*` | Create | Unit, mocked integration, snapshots, optional golden audio warning. |
| `scripts/validate_manifest.py` | Create | CLI JSONL schema validator. |
| `pyproject.toml` | Create | Ruff, pytest, package metadata, optional mypy config. |
| `requirements.txt` | Create | Colab/runtime pins. |
| `README.md` | Modify | Usage plus AI-generated/personal-use disclaimer. |

Recommended tree: `notebooks/tts_pipeline.ipynb`; `src/texttovoz/{__init__,pipeline,ingest,normalize,tokenize,chunk,tts,manifest,audio_io,config}.py`; `src/texttovoz/data/acronyms.yaml`; `tests/{conftest,test_normalize,test_tokenize,test_chunk,test_manifest,test_audio_io,test_pipeline_smoke}.py`; `tests/snapshots/`; `scripts/validate_manifest.py`; `pyproject.toml`; `requirements.txt`; `README.md`.

## Interfaces / Contracts

Manifest path is `chunks/manifest.jsonl`, one JSON object per line:

```jsonl
{"chunk_id": 1, "text": "...", "text_hash": "sha256:...", "audio_path": "chunks/chunk_001.wav", "duration_s": 2.31, "sample_rate": 24000, "channels": 1, "watermark_present": true, "language_id": "es", "model_id": "ResembleAI/Chatterbox-Multilingual-es-mx-latam", "exaggeration": 0.5, "cfg_weight": 0.5, "temperature": 0.8, "seed": 42, "status": "success|pending|error", "generated_at": "2026-07-01T...", "error": null}
```

Dependencies: Python >=3.10; `chatterbox-tts==0.1.7` (observed in `explore.md`), `torch==2.6.0`, `torchaudio==2.6.0`, `transformers==5.2.0`, `spacy`, `es_core_news_sm`, `numpy`, `soundfile`, `pydantic>=2`, `pytest`, `ruff`, `tqdm`, `pyyaml`. Chatterbox wrapper must assert `watermark_present is True` at startup/config validation.

## Testing Strategy

| Layer | What to Test | Approach |
|---|---|---|
| Unit | `normalize.py` acronym expansion, whitespace, edge chars; `tokenize.py` Spanish fixture corpus and first 200 chars of target subtitle; `chunk.py` 280-char cap/no mid-sentence split; `manifest.py` Pydantic v2 schema and append-only JSONL; `audio_io.py` silence gap and mono mixdown. | `pytest` local, no GPU. |
| Integration | Full pipeline orchestration with Chatterbox mocked. | Snapshot `tests/snapshots/manifest.jsonl`. |
| Audio regression | Tiny fixed text + fixed seed → `tests/snapshots/chunk_001.wav`. | Warn on byte drift, do not fail, because Chatterbox determinism varies by library/hardware. |
| Lint/format | Ruff strict rules `E,F,I,B,UP`; no `noqa`; `ruff format`. | CI and verify phase. |
| Notebook smoke | Kernel boots and a 2-line smoke notebook executes. | `jupyter nbconvert --execute`, slow; run on `main` only. |
| Manifest validation | Existing JSONL conforms to schema. | `python scripts/validate_manifest.py output/manifest.jsonl` or `chunks/manifest.jsonl` for chunk output. |

Exact verify commands:

```bash
ruff check .
ruff format --check .
pytest -q
pytest -q tests/test_pipeline_smoke.py
python scripts/validate_manifest.py output/manifest.jsonl
```

Optional type checking: `mypy --strict src/`, off by default due small codebase and Colab velocity.

## Migration / Rollout

No data migration required. Rollout is local-only: implement package/tests, then notebook, then README disclaimer. Generated local artifacts (`chunks/`, `output/`) should remain uncommitted.

## Risks & Mitigations

| Risk | Probability × Impact | Mitigation |
|---|---|---|
| Colab disconnect mid-run | Medium × High | Resume from manifest, skip `success` rows with matching hash. |
| VRAM OOM from expressive settings | Medium × Medium | Default `exaggeration=0.5`, `cfg_weight=0.5`; document lower settings and shorter chunk cap. |
| Library API drift | Medium × High | Pin `chatterbox-tts==0.1.7`; document upgrade as a task: update pins, rerun smoke/golden/manual preview. |
| Watermark disabled by mistake | Low × High | Config default `True`, startup assertion, manifest `watermark_present: true`. |
| Spanish tokenizer mismatch | Medium × Medium | Fixture corpus plus actual subtitle first 200 chars in tests. |
| Voice cloning slip-in | Low × High | No cloning in MVP; future consent gate hook blocks reference audio unless explicit opt-in. |

## Open Questions

- [ ] Confirm exact public loader path for `ResembleAI/Chatterbox-Multilingual-es-mx-latam` during implementation.
- [ ] Decide whether final manifest validator path should target `chunks/manifest.jsonl`, `output/manifest.jsonl`, or copy chunk manifest to output during export.

## Spec-kit Mapping

- SK-SPEC-001 ↔ `ingest.py` and notebook cell 3 path config.
- SK-SPEC-002 ↔ `normalize.py` and `data/acronyms.yaml`.
- SK-SPEC-003 ↔ `tokenize.py`.
- SK-SPEC-004 ↔ `chunk.py`.
- SK-SPEC-005 ↔ `tts.py` and `pipeline.py`.
- SK-SPEC-006 ↔ `config.py`, `tts.py`, `manifest.py` watermark assertion.
- SK-SPEC-007 ↔ `manifest.py` Pydantic JSONL schema.
- SK-SPEC-008 ↔ `pipeline.py` resume and `argparse` slice CLI.
- SK-SPEC-009 ↔ `audio_io.py` concat/export.
- SK-SPEC-010 ↔ notebook preview branch with `IPython.display.Audio`.
- SK-SPEC-011 ↔ notebook markdown and README disclaimer.
- SK-SPEC-012 ↔ seed config and manifest fields.
- SK-SPEC-013 ↔ per-chunk error handling in `pipeline.py`.
- SK-SPEC-014 ↔ Colab cells, HF cache, dependency pins.
- SK-SPEC-015 ↔ manifest hash/status idempotency.
- SK-SPEC-016 ↔ deferred consent gate in config/notebook.
