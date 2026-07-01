# Exploration: texttovoz-tts-pipeline

## Executive summary

The requested pipeline is feasible as a specs-first, Google Colab-runnable Python/Jupyter project: ingest `/home/mackroph/Descargas/subtitle.txt`, normalize/chunk Spanish prose, synthesize each chunk with Resemble AI Chatterbox, and join/export audio. Chatterbox remains the recommended primary TTS engine because the targeted Hugging Face model `ResembleAI/Chatterbox-Multilingual-es-mx-latam` exists, is MIT licensed, is optimized for Latin American/Mexican Spanish, supports voice cloning, and fits the likely Colab GPU class if used carefully.

Key risks are not architectural; they are operational and quality-related: Chatterbox examples and the LatAm demo cap input at 300 characters per generation, so the 16.3k-character transcript MUST be sentence-aware chunked; voice cloning MUST require user-owned/authorized reference audio; Colab free-tier resources are not guaranteed and content-generation/web-UI patterns can be terminated; Chatterbox applies built-in PerTh watermarking, so outputs should be treated as AI-generated and watermarked.

Recommended path forward: write SDD specs for a notebook-only MVP with deterministic preprocessing, previewable chunks, explicit consent checks for voice reference audio, per-chunk WAV generation, manifest logging, and final concatenation/export. Do not implement code yet.

## Current state

- Repository currently contains only notebook scaffolding and project instructions:
  - `AGENTS.md` — Python 3.10+, Jupyter notebook conventions, work in `notebooks/`.
  - `README.md` — project overview placeholder.
  - `notebooks/.gitkeep` — notebook workspace placeholder.
- `openspec/config.yaml` and `openspec/specs/` were not present during exploration; this change folder was created only to persist this artifact.
- User requested specs/proposals/designs only; no notebook or Python module should be created in this phase.

## Affected areas

- `openspec/changes/texttovoz-tts-pipeline/` — active SDD change artifacts only.
- Future phases will likely specify notebook work under `notebooks/`, but exploration made no code changes.
- Future dependency declarations may affect `requirements.txt` or equivalent, but only after proposal/spec/design/tasks and apply phases.

## Subtitle analysis

### File inspected

- Path: `/home/mackroph/Descargas/subtitle.txt`
- Encoding observed: UTF-8
- Shape: 1 physical line, plain prose

### Stats

| Metric | Value |
|---|---:|
| Characters | 16,347 |
| UTF-8 bytes | 16,716 |
| Approx. words | 2,823 |
| Approx. token estimate | ~3,670 to ~4,087 tokens |
| Physical lines | 1 |
| Sentence-like segments | 179 |
| Avg sentence length | 90.3 chars |
| Max sentence length | 358 chars |
| Sentences >200 chars | 16 |
| Sentences >300 chars | 3 |

### Language and variant

- Language: Spanish.
- Variant: mostly neutral Latin American educational Spanish with some informal/direct-address phrasing (`puedes`, `vamos`, `empecemos`) and technical vocabulary. It is not strongly Argentinian (`vos`, `ustedes`-only regional markers, lunfardo) and not clearly Peninsular Spanish; `vídeo` appears, which is common in Spain and also accepted elsewhere, but the overall text is neutral/mixed LatAm.
- Target model fit: the `es-419 / es-MX` LatAm model is appropriate; it should sound more natural for broad LatAm than a Spain-specific model.

### Content structure and markers

- Plain prose transcript about ASP.NET Core routing and APIs.
- No timestamps detected.
- No speaker tags detected.
- No URLs detected.
- No Markdown headers, bullets, or code fences detected.
- Contains technical terms and acronyms: `ASP.NET`, `API`, `ID`, `HTTP`, `URL`, `JPG`.
- Contains numbers: repeated `10`, plus `1`, `0`, `2016`, `2024`, `404`.
- Non-ASCII characters are expected Spanish punctuation/accents: `¿áéíñóú`.
- No very long words over 25 characters were detected.

### Normalization needs

The spec should require a preprocessing stage before TTS:

- Normalize whitespace from one long line into sentence-aware segments.
- Preserve sentence-ending punctuation because it affects prosody.
- Expand or pronounce acronyms intentionally:
  - `API` likely as “a pe i” or “API” depending desired narration style.
  - `ASP.NET` likely “A S P punto net” or “ASP dot net”; user should decide if Spanish or English-style pronunciation is preferred.
  - `HTTP`, `URL`, `ID`, `JPG` should be mapped explicitly.
- Convert important numbers to Spanish words where natural:
  - HTTP status `404` may be “cuatro cero cuatro” or “error cuatrocientos cuatro”; user should choose style.
  - years `2016`, `2024` likely “dos mil dieciséis”, “dos mil veinticuatro”.
  - route values like `0`, `1`, `10` may remain digits in manifests but should be spoken as words.
- Avoid SSML-like tags unless verified later; Chatterbox docs reviewed here do not advertise SSML support for multilingual V3. Turbo supports paralinguistic bracket tags, but Turbo is English-only in the model zoo and not the target model.

### Recommended chunking strategy

Evidence:

- Chatterbox source does not expose a formal `generate()` character limit in the API docs, but the official LatAm Spanish demo truncates with `text_input[:300]` and labels the UI “max chars 300”.
- The inspected subtitle has 3 sentence-like segments longer than 300 characters and 16 over 200 characters.

Requirement recommendation:

- Hard cap generated chunks at **≤300 characters** until real quality testing proves a higher limit is safe.
- Prefer target chunk size **180–260 characters** for prosody and retry safety.
- Split first by sentence boundaries (`.`, `?`, `!`), then merge short adjacent sentences without crossing 300 chars.
- If an individual sentence exceeds 300 chars, split on semicolons, commas, conjunctions, or clause boundaries; never split inside acronyms like `ASP.NET` or decimal-like technical tokens.
- Persist a chunk manifest with original text span, normalized text, character count, output audio filename, generation settings, and any warnings.

## Chatterbox API snapshot

Sources used:

- Context7 library ID: `/resemble-ai/chatterbox`
- Context7 docs cited: README, `_autodocs/chatterbox-multilingual-api.md`, `_autodocs/configuration.md`, `_autodocs/errors.md`
- PyPI JSON for `chatterbox-tts`
- GitHub source files `src/chatterbox/mtl_tts.py`, `src/chatterbox/tts.py`, `src/chatterbox/models/s3gen/const.py`
- Hugging Face model card/API for `ResembleAI/Chatterbox-Multilingual-es-mx-latam`

### Package and version

- Install package: `chatterbox-tts`
- Current PyPI version observed: **0.1.7**
- Python requirement: `>=3.10`
- Core pinned deps from PyPI/source include `torch==2.6.0`, `torchaudio==2.6.0`, `librosa==0.11.0`, `transformers==5.2.0`, `diffusers==0.29.0`, `safetensors==0.5.3`, and `resemble-perth`.
- License: MIT for package and target HF model.

### Multilingual model loading

Documented API:

- `ChatterboxMultilingualTTS.from_pretrained(device, t3_model=None)`
- `device`: `"cuda"`, `"cpu"`, or `"mps"`
- `t3_model` accepted variants from Context7/source:
  - `None` → default multilingual V2 (`t3_mtl23ls_v2.safetensors`)
  - `"v2"`, `"t3_mtl23ls_v2"`
  - `"v3"`, `"t3_mtl23ls_v3"`
  - explicit `.safetensors` filename

Recommendation:

- Use multilingual V3 behavior for this project. For the dedicated LatAm single-language checkpoint, the proposal/design phase must verify the correct loader path because the HF demo imports `ChatterboxTTS` from an internal path but passes `language_id="es"`, while the general public docs show `ChatterboxMultilingualTTS` for multilingual use. This is a loader/API ambiguity, not a blocker, but it must be resolved before implementation.

### Generation API

Context7 documented multilingual signature:

- `generate(text, language_id, audio_prompt_path=None, exaggeration=0.5, cfg_weight=0.5, temperature=0.8, repetition_penalty=1.2, min_p=0.05, top_p=1.0)`

Source behavior:

- Validates `language_id` against 23 two-letter codes.
- Normalizes punctuation internally via `punc_norm`.
- Requires existing conditionals or `audio_prompt_path`; without either, multilingual source asserts that conditionals must be prepared first.
- Applies PerTh watermark before returning.
- Returns `torch.from_numpy(watermarked_wav).unsqueeze(0)`, i.e. a tensor shaped like `[1, samples]`.

Recommended initial generation parameters:

- `language_id="es"`
- `exaggeration=0.5`
- `cfg_weight=0.5`
- `temperature=0.8`
- `repetition_penalty=1.2`
- `min_p=0.05`
- `top_p=1.0`
- If the reference speaker is too fast, test `cfg_weight≈0.3` per README guidance.
- For more expressive narration, test `exaggeration≈0.7` with lower `cfg_weight`, but only after baseline is accepted.

### Language support

- Supported multilingual language IDs include: `ar`, `da`, `de`, `el`, `en`, `es`, `fi`, `fr`, `he`, `hi`, `it`, `ja`, `ko`, `ms`, `nl`, `no`, `pl`, `pt`, `ru`, `sv`, `sw`, `tr`, `zh`.
- Spanish variants do not use separate `language_id` values; target LatAm behavior comes from the dedicated model assets. The HF target model card states:
  - Locale: `es-419 / es-MX`
  - Chatterbox language ID: `es`

### Output and save behavior

- Sample rate: **24,000 Hz** (`S3GEN_SR = 24000`).
- Output tensor: `[1, samples]` per source return.
- Save API shown in docs: `torchaudio.save(..., wav, model.sr)`.
- For notebook specs, require per-chunk WAV files and a final concatenated WAV; MP3 export can be optional if ffmpeg/pydub is included later.

### Watermarking

- Chatterbox README states every generated audio file includes Resemble AI PerTh perceptual watermarking.
- Source applies `PerthImplicitWatermarker.apply_watermark(...)` inside `generate()`.
- Treat watermarking as built-in and non-optional unless future docs prove a supported opt-out exists.

### Text length and SSML/tag behavior

- No formal maximum was found in Context7 API docs.
- Official LatAm Space truncates text to 300 chars and labels input “max chars 300”; use 300 chars as the practical cap.
- Multilingual docs do not advertise SSML support.
- Chatterbox-Turbo docs mention paralinguistic tags like `[laugh]`, but Turbo is English-only; do not assume these tags are supported by the LatAm multilingual model.

## Hugging Face target model snapshot

Model: `ResembleAI/Chatterbox-Multilingual-es-mx-latam`

- Exists and is public.
- License: MIT.
- Task/library tags: text-to-speech, Chatterbox, Spanish, multilingual, single-language-tts, voice-cloning, chatterbox-v3.
- Purpose: dedicated single-language finetune in Chatterbox Multilingual V3 Single Language Pack.
- Region/locale: Latin American Spanish / Mexico (`es-419 / es-MX`).
- Language ID: `es`.
- Stated benefit: tighter Latin American Spanish quality control than the broad multilingual checkpoint.
- Files listed:
  - `t3_es_mx_latam.safetensors`
  - `s3gen_v3.pt`
  - `s3gen_v3.safetensors`
  - `grapheme_mtl_merged_expanded_v1.json`
- Checkpoint metadata from card:
  - T3 tensor count: 292
  - dtype: float32
  - T3 size: 2,143,990,280 bytes (~2.14 GB)
  - HF API `usedStorage`: 4,257,275,778 bytes (~4.26 GB) for repository assets
  - SHA256 for T3: `c66c4517f11c2b35a56e28615c0689deb864cbc411e329552223bbd0a6a063f8`

## Colab fit

### Runtime constraints

- Official Colab FAQ confirms free Colab offers GPUs but resources, GPU types, idle timeouts, and maximum lifetimes vary and are not guaranteed.
- Official FAQ states free notebooks can run at most 12 hours depending on availability/usage patterns and will time out when idle.
- The commonly available free GPU for this use case is expected to be NVIDIA T4 with 16 GB VRAM, but Colab does not guarantee a specific GPU type.
- Colab free-tier restrictions explicitly disallow creating deepfakes and may terminate popular content-generation workflows that bypass the notebook UI or primarily use a web UI.

### Model and disk fit

- Target HF model repository storage: ~4.26 GB.
- T3 LatAm checkpoint alone: ~2.14 GB float32.
- General Chatterbox multilingual is a ~500M model class; source/PyPI dependencies include Torch/Torchaudio and may add substantial install size.
- Practical Colab disk recommendation: reserve at least **8–12 GB** free for package wheels, Hugging Face cache, intermediate WAV chunks, final audio, and retry artifacts.
- VRAM risk: likely acceptable on T4 16 GB for 300-character chunks, but must be verified in the later implementation/verification phases because the single-language loader path and exact runtime memory were not executed here.

### Storage strategy

- Keep generation scratch files local to the Colab VM for speed.
- Save durable artifacts to Google Drive only after generation or at safe checkpoints:
  - chunk manifest
  - per-chunk WAVs if user wants resumability
  - final WAV/MP3 output
- Avoid many tiny Drive I/O operations; official Colab FAQ warns Drive can time out or fail with many files or high quota pressure.
- Provide a notebook download option for the final audio if Drive is not mounted.

### Install/cold-start recommendation

For future design/tasks, specify a minimal cold-start sequence:

1. Confirm GPU availability and Python version.
2. Install/pin `chatterbox-tts==0.1.7` first, because it pins Torch/Torchaudio and related deps.
3. Install small preprocessing/export helpers after Chatterbox, such as `num2words`, optional `spacy`, and optional audio concatenation/export dependencies.
4. Download/load model once; cache under the default Hugging Face cache or Drive only if the added persistence complexity is worth it.

## Alternatives verdict

| Alternative | Strengths | Risks / caveats | Verdict |
|---|---|---|---|
| Chatterbox LatAm Spanish | MIT package/model, dedicated `es-419 / es-MX` checkpoint, voice cloning, modern 2026 package, built-in watermarking, likely Colab GPU fit | Loader ambiguity for single-language pack; 300-char practical cap; built-in watermark may be a product constraint | Recommended |
| Coqui XTTS-v2 | Mature ecosystem, 17 languages, 24 kHz, voice cloning from short reference, huge usage | HF model license is Coqui Public Model License, not MIT; PyPI `TTS` latest 0.22.0 is from Dec 2023 and requires Python `<3.12`; less targeted LatAm checkpoint | Not primary due license and maintenance fit |
| `jpgallegoar/F5-Spanish` | Spanish-specific, includes several LatAm datasets, Colab instructions mention T4 | HF page shows license badge `cc-by-nc-4.0` while card text says CC0-1.0, creating license ambiguity; usage is less packaged/direct; likely more manual | Promising quality candidate, but not safer than Chatterbox for MIT requirement |
| Piper TTS | Fast/local, MIT in archived rhasspy repo, efficient CPU-friendly | Original repo archived Oct 2025 and moved to GPL successor; no voice cloning; less expressive/neural-cloning quality; Spanish voices depend on available voice model | Good fallback for deterministic offline TTS, not for requested quality/voice cloning |

Conclusion: Chatterbox wins for the stated use case: LatAm Spanish quality, MIT licensing, modern active model/package, voice cloning, watermarked responsible AI behavior, and likely Colab T4 feasibility.

## Text-preprocessing for TTS

Recommended preprocessing stack for specs/design:

- Sentence segmentation:
  - Start with spaCy Spanish or a rule-based Spanish sentencizer.
  - Context7 spaCy docs confirm the `Sentencizer` is a rule-based sentence boundary component that assigns `Token.is_sent_start` and exposes `Doc.sents`; this is sufficient if dependency parsing is not required.
  - For a lightweight notebook MVP, a custom punctuation-aware splitter may be acceptable if tests cover acronyms like `ASP.NET` and abbreviations.
- Number normalization:
  - Use `num2words` for Spanish numbers where natural, with custom rules for years, HTTP codes, route IDs, decimals, and version-like tokens.
- Acronym normalization:
  - Use an explicit mapping table for technical transcript terms (`API`, `ASP.NET`, `HTTP`, `URL`, `ID`, `JPG`) rather than relying on generic TTS pronunciation.
- URL/code handling:
  - Current subtitle has no URLs or code fences, but specs should require detection and safe handling: summarize/skip URLs, verbalize code tokens only when user chooses, and preserve technical examples in a pronounceable form.
- Punctuation:
  - Preserve `¿?`, `¡!`, periods, and commas where possible.
  - Avoid excessive semicolon/colon/em dash usage because Chatterbox source internally replaces some punctuation (`:`, `;`, em dash, ellipsis) during normalization.

## Mapping to GitHub spec-kit methodology

Spec-kit source: GitHub `github/spec-kit` README fetched during exploration. It describes core commands `/speckit.specify`, `/speckit.plan`, `/speckit.tasks`, and `/speckit.implement`, plus optional clarification/analyze/checklist flows.

| spec-kit concept/artifact | Purpose in spec-kit | SDD/OpenSpec equivalent for this project | Notes |
|---|---|---|---|
| `specify` / `spec.md` | Define what and why; user stories and functional requirements | `proposal.md` + delta specs under `openspec/changes/texttovoz-tts-pipeline/specs/.../spec.md` | Our proposal captures intent/scope; our spec captures normative requirements/scenarios. |
| `clarify` | Resolve underspecified requirements before planning | Open questions in explore/proposal, plus spec clarification before design | Use only if proposal/spec cannot proceed without user answers. |
| `plan` / `plan.md`, `research.md`, implementation detail docs | Technical implementation approach and decisions | `design.md` plus this `explore.md` as research input | This exploration mirrors spec-kit `research.md`; design mirrors `plan.md`. |
| `tasks` / `tasks.md` | Actionable implementation task list | `openspec/changes/texttovoz-tts-pipeline/tasks.md` | Should include notebook-only tasks and verification tasks. |
| `implement` | Execute tasks | Later SDD `apply` phase | Not part of this user request. |
| `analyze` / checklist | Cross-artifact consistency and readiness checks | Later SDD `verify` phase and optional checklist inside specs/tasks | Robust verification will run after implementation. |

Spec-kit-specific artifacts worth mirroring in OpenSpec:

- Keep this exploration as the equivalent of `research.md`.
- Ensure `proposal.md` states user scenarios and non-goals clearly.
- Ensure `design.md` includes an implementation plan, risk decisions, and notebook/runtime constraints.
- Ensure `tasks.md` is ordered by user-visible workflow: input → preprocessing → chunk preview → model setup → generation → export → verification.

## Approaches

1. **Notebook-first Chatterbox LatAm MVP** — One Colab-compatible notebook specified to preprocess the local transcript, chunk it, synthesize chunks using Chatterbox LatAm Spanish, and export final audio.
   - Pros: Matches project conventions; simplest user workflow; lowest repo complexity; aligns with Colab target.
   - Cons: Notebook reproducibility can degrade without careful manifests and pinned dependencies.
   - Effort: Medium.

2. **Notebook plus reusable Python module** — Put stable preprocessing/generation helpers into a module and keep notebook as orchestration UI.
   - Pros: More testable and reusable; cleaner long-term architecture.
   - Cons: User requested specs only now and project convention says promote notebook logic to modules only when stable/reused.
   - Effort: Medium-High.

3. **External TTS abstraction layer** — Specify a provider interface supporting Chatterbox, XTTS, F5, and Piper.
   - Pros: Easy model swapping.
   - Cons: Over-engineered for MVP; increases dependencies and spec surface; weakens focus on Chatterbox-specific LatAm quality.
   - Effort: High.

## Recommendation

Proceed with **Notebook-first Chatterbox LatAm MVP** in the proposal/spec/design phases. Specify clean boundaries inside the notebook (preprocess, chunk, synthesize, export, verify) and require a manifest so the implementation can later be promoted to modules if reuse emerges. Keep Chatterbox as the primary engine and document alternatives only as non-goals/fallback context.

## Risks

- **Text-length handling: Medium.** The source transcript is 16,347 chars and official LatAm demo caps text at 300 chars, so chunking is mandatory. Risk is manageable with sentence-aware chunking and manifest-driven retries.
- **Voice cloning legal/ethical use: Medium-High.** The model supports voice cloning and Colab prohibits deepfakes. Specs must require user-owned/authorized reference audio and visible consent/disclaimer language.
- **Colab free-tier VRAM/licensing: Medium.** MIT licensing is favorable; target assets are ~4.26 GB and likely fit T4 16 GB with short chunks, but Colab resources/GPU type are not guaranteed and runtime termination is possible.
- **Watermarking requirements: Low-Medium.** Built-in PerTh watermarking is good for responsible AI, but if the user expects unwatermarked audio, Chatterbox may not satisfy that requirement. No opt-out was verified.
- **Single-language loader ambiguity: Medium.** Public docs emphasize `ChatterboxMultilingualTTS`, while the HF demo uses an internal `ChatterboxTTS` import with `language_id="es"`; implementation must verify the correct public loading path for `ResembleAI/Chatterbox-Multilingual-es-mx-latam`.

## Open questions for proposal/spec phases

1. What voice should be used: built-in/default voice or a user-provided reference audio file?
2. If using a reference voice, does the user confirm they own it or have explicit permission to clone it?
3. Preferred pronunciation style for technical acronyms: Spanish letter names, English-style developer pronunciation, or custom glossary?
4. Preferred output format: WAV only, MP3 too, or both?
5. Should the notebook save all per-chunk WAV files for resumability, or only the final joined audio plus manifest?
6. Should the transcript be treated as copyrighted/third-party course content, and is generated narration for personal use only?
7. Should the final audio target neutral LatAm narration or explicitly Mexican Spanish tone?

## Ready for proposal

Yes. The proposal can proceed without blocking if it records the open questions as assumptions/defaults:

- Default to Chatterbox LatAm Spanish, `language_id="es"`, 300-character max chunks, WAV output, manifest logging, and explicit consent requirement for any voice reference.
- Defer actual model execution, loader verification, and audio quality checks to later apply/verify phases.
