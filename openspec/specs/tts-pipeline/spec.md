# TTS Pipeline Specification

## Purpose

Define the notebook-first MVP behavior for ingesting a Spanish transcript, normalizing and chunking it, generating Chatterbox LatAm Spanish audio, resuming safely, and exporting a final WAV.

## Spec-kit Mapping

| spec_id | Requirement |
|---|---|
| SK-SPEC-001 | Input Ingest |
| SK-SPEC-002 | Text Normalization |
| SK-SPEC-003 | Sentence Tokenization |
| SK-SPEC-004 | Chunking |
| SK-SPEC-005 | TTS Generation |
| SK-SPEC-006 | Watermarking |
| SK-SPEC-007 | Manifest Emission |
| SK-SPEC-008 | Resume and Slice Regeneration |
| SK-SPEC-009 | Output Export |
| SK-SPEC-010 | Preview |
| SK-SPEC-011 | Disclaimer and Personal Use |
| SK-SPEC-012 | Reproducibility |
| SK-SPEC-013 | Failure Isolation |
| SK-SPEC-014 | Colab Fit and Cold Start |
| SK-SPEC-015 | Idempotent Rerun |
| SK-SPEC-016 | Consent Gate Deferred Hook |

## Requirements

### Requirement: Input Ingest

The system SHALL load `/home/mackroph/Descargas/subtitle.txt` as UTF-8 text and SHALL reject missing files, non-UTF-8 content, or empty effective input with a clear user-visible error.

#### Scenario: Valid UTF-8 subtitle is loaded

- GIVEN the subtitle file exists and is UTF-8
- WHEN ingest runs
- THEN the transcript text is available for normalization

#### Scenario: Invalid ingest input is rejected

- GIVEN the file is missing, not UTF-8, or produces zero usable text
- WHEN ingest runs
- THEN no TTS generation starts
- AND the error names the failed condition

### Requirement: Text Normalization

The system SHALL normalize whitespace, trim non-printable characters, preserve Spanish punctuation including `¿` and `¡`, and expand acronyms using a configurable glossary whose default spells out `ASP.NET`, `API`, `HTTP`, `URL`, and `ID`.

#### Scenario: Acronyms and punctuation are preserved for speech

- GIVEN text contains an acronym at the start or end of a sentence and Spanish punctuation
- WHEN normalization runs
- THEN the acronym is replaced by the glossary form
- AND Spanish punctuation remains present

#### Scenario: Empty or punctuation-only content is excluded

- GIVEN a normalized segment has no speakable content
- WHEN sentence preparation runs
- THEN the segment is not sent to TTS

### Requirement: Sentence Tokenization

The system SHALL split Spanish text into sentence units and SHALL enforce a default maximum sentence length of 280 characters.

#### Scenario: Spanish sentence boundaries are detected

- GIVEN normalized Spanish prose with `.`, `?`, `!`, `¿`, or `¡`
- WHEN tokenization runs
- THEN observable sentence records are produced

#### Scenario: Sentence exceeds cap

- GIVEN a sentence exceeds 280 characters
- WHEN tokenization runs
- THEN it is split at clause boundaries where possible
- AND hard-split fallback keeps every unit within the cap

### Requirement: Chunking

The system SHALL group sentences into chunks of 280 characters or fewer by default and SHALL NOT split a sentence across chunks after tokenization.

#### Scenario: Sentences are grouped without boundary loss

- GIVEN tokenized sentences whose combined length may exceed the cap
- WHEN chunking runs
- THEN each chunk is at or below the cap
- AND sentence boundaries remain intact

### Requirement: TTS Generation

The system SHALL generate audio chunk-by-chunk with Chatterbox Multilingual TTS, `language_id="es"`, and the default LatAm ES checkpoint, returning an audio tensor and sample rate per chunk.

#### Scenario: Successful chunk generation

- GIVEN a valid chunk and loaded model
- WHEN generation runs
- THEN an audio tensor and sample rate are produced
- AND generation settings are observable for the chunk

#### Scenario: Model load or runtime generation fails

- GIVEN model loading fails, CUDA OOM occurs, or runtime disconnect interrupts a chunk
- WHEN generation is attempted
- THEN the failure is recorded for that chunk

### Requirement: Watermarking

The system MUST NOT disable Chatterbox watermarking and SHALL declare every generated WAV as watermarked in the manifest.

#### Scenario: Watermark declaration is persisted

- GIVEN a chunk WAV is generated
- WHEN the manifest entry is written
- THEN `watermark_present` is `true`

### Requirement: Manifest Emission

The system SHALL emit JSONL at `chunks/manifest.jsonl` with `chunk_id`, `text`, `text_hash`, `audio_path`, `duration_s`, `sample_rate`, `channels`, `watermark_present`, `language_id`, `model_id`, `exaggeration`, `cfg_weight`, `temperature`, `status`, `generated_at`, and `error` per chunk.

#### Scenario: Successful chunk manifest row

- GIVEN a chunk succeeds
- WHEN its manifest row is emitted
- THEN required fields are present
- AND `status` is `success` with empty error

#### Scenario: Manifest path collision

- GIVEN `chunks/manifest.jsonl` exists from an unrelated run
- WHEN a new run starts
- THEN the default behavior is to refuse with an explicit collision message

### Requirement: Resume and Slice Regeneration

The system SHALL skip manifest entries with `status: success`, regenerate entries with `status: pending` or `status: error`, and support bounded runs from `from_chunk` N to `to_chunk` M.

#### Scenario: Resume skips successful chunks

- GIVEN a manifest contains successful and failed entries
- WHEN the notebook reruns
- THEN successful chunks are not regenerated
- AND pending or error chunks are attempted

#### Scenario: Slice regeneration limits work

- GIVEN `from_chunk` and `to_chunk` are set
- WHEN generation runs
- THEN only chunks in that inclusive range are eligible

### Requirement: Output Export

The system SHALL concatenate successful chunk WAVs into `output/full.wav` as 24 kHz mono with a default 100 ms silence gap between chunks.

#### Scenario: Final WAV export succeeds

- GIVEN all required chunks have successful WAVs
- WHEN export runs
- THEN `output/full.wav` exists
- AND it is 24 kHz mono with configured gaps

### Requirement: Preview

The system SHALL display the first one or two generated chunks inline with `IPython.display.Audio` before full generation continues.

#### Scenario: User can sanity-check prosody

- GIVEN preview chunks are generated
- WHEN preview mode runs
- THEN inline audio players are visible in the notebook

### Requirement: Disclaimer and Personal Use

The notebook SHALL display an “AI-generated audio” notice for any non-personal use and SHALL constrain the MVP to personal use only.

#### Scenario: Responsible-use notice is visible

- GIVEN the notebook is opened or run
- WHEN usage guidance is shown
- THEN personal-use-only and AI-generated-audio notices are visible

### Requirement: Reproducibility

The system SHALL produce identical per-chunk output bytes when input text, normalized text, settings, model, environment, and seed are identical.

#### Scenario: Same seed produces same chunk bytes

- GIVEN identical inputs and seed
- WHEN the same chunk is generated twice without resume skipping
- THEN the chunk audio bytes match

### Requirement: Failure Isolation

The system SHALL NOT abort the full run because one chunk fails; it SHALL record `status: error` and an error message, then continue with later eligible chunks.

#### Scenario: CUDA OOM affects one chunk only

- GIVEN one chunk raises CUDA OOM
- WHEN generation continues
- THEN that chunk is marked error
- AND later chunks are still attempted

### Requirement: Colab Fit and Cold Start

The system SHALL fit a free-tier Colab T4 target with 16 GB VRAM, cache checkpoints under `/content/.cache/huggingface`, and SHOULD keep fresh install plus checkpoint pull within about 10 minutes.

#### Scenario: Colab runtime uses cached checkpoint path

- GIVEN a fresh Colab runtime
- WHEN dependencies and model assets are prepared
- THEN checkpoint cache location is `/content/.cache/huggingface`

### Requirement: Idempotent Rerun

The system SHALL make crash recovery idempotent so rerunning the notebook yields the same completed output without regenerating already-successful chunks.

#### Scenario: Runtime disconnect mid-run recovers

- GIVEN a manifest exists after a disconnect
- WHEN the notebook is rerun
- THEN successful chunks remain untouched
- AND incomplete chunks are completed or marked error

### Requirement: Consent Gate Deferred Hook

If voice cloning is later enabled, the notebook MUST require explicit confirmation of consent before any cloning reference audio is processed.

#### Scenario: Future cloning cannot proceed without consent

- GIVEN voice cloning mode is enabled in a later version
- WHEN reference audio is selected without explicit consent
- THEN cloning audio processing is blocked
