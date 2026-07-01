# Proposal: TextTovoz TTS Pipeline

## Intent

Create a notebook-first MVP that turns `/home/mackroph/Descargas/subtitle.txt` into Spanish narration with Chatterbox LatAm Spanish. Use is personal/experimental only, with resumable chunks and responsible-AI safeguards.

## Scope

### In Scope
- Colab/Jupyter flow: input → preprocess → chunk → Chatterbox TTS → JSONL manifest → WAV export.
- Default Chatterbox multilingual voice, no cloning, `language_id="es"`, HF model `ResembleAI/Chatterbox-Multilingual-es-mx-latam`.
- Acronym spelling via flag/glossary, e.g. `ASP.NET` → `A-S-P punto N-E-T`; `API`, `HTTP`, `URL`, `ID` as letters.
- WAV 24 kHz mono; save chunks as `chunks/chunk_NNN.wav`.
- JSONL manifest: text, duration, hash, status, `watermark_present: true`.

### Out of Scope
- Voice cloning in MVP; future opt-in requires consent capture and authorized audio.
- Redistribution pipeline, public hosting, or publishing generated audio from third-party tutorial content.
- MP3 export in MVP; architecture must allow later formats without TTS rewrite.

## Capabilities

### New Capabilities
- `tts-pipeline`: Preprocessing, chunked TTS, resumable manifesting, WAV export.

### Modified Capabilities
- None; no existing `openspec/specs/` capabilities are present.

## Approach

One notebook: load transcript, normalize whitespace/acronyms/numbers, sentence-aware chunk, generate chunk WAVs, append manifest, resume incomplete chunks, concatenate/export final WAV.

## Affected Areas

| Area | Impact | Description |
|---|---|---|
| `openspec/changes/texttovoz-tts-pipeline/` | Modified | SDD artifacts. |
| `notebooks/` | Future modified | MVP notebook implementation target. |
| `requirements.txt`/`pyproject.toml` | Future modified | TTS/helper dependencies. |
| `README.md` / `AGENTS.md` | Future possible | Usage/disclaimer notes if needed. |

## Risks

| Risk | Likelihood | Mitigation |
|---|---:|---|
| Text-length/prosody limits | Med | Sentence-aware chunks; ≤300-char cap. |
| Voice cloning misuse | Med | Deferred; future consent gate. |
| Transcript copyright | Med | Personal use only; no hosting/redistribution. |
| Colab GPU/session limits | Med | Chunk persistence and resume. |
| Watermark/disclosure | Low-Med | PerTh on; public use needs AI disclaimer. |

## Spec-kit Alignment

| spec-kit | SDD/OpenSpec here |
|---|---|
| `specify` | `proposal.md` + delta spec |
| `plan` | `design.md` |
| `tasks` | `tasks.md` |

## Rollback Plan

Remove notebook/dependency/doc changes and local audio artifacts (`chunks/`, manifest, final WAV). No app behavior or service data changes.

## Dependencies

- `chatterbox-tts`, PyTorch/Torchaudio, target HF model, preprocessing/audio helpers.
- Local transcript and Colab/Jupyter runtime with disk/GPU.

## Success Criteria

- [ ] Transcript becomes resumable chunk WAVs plus final 24 kHz mono WAV.
- [ ] Manifest restarts without regenerating successful chunks.
- [ ] Acronym spelling can be toggled off.
- [ ] Responsible-AI/copyright constraints are visible.

## Open Questions for Spec Phase

- Exact manifest schema and hash inputs.
- First acronym/number glossary.
- Public loader path for LatAm checkpoint.
- Whether README/AGENTS need usage/disclaimer updates.
