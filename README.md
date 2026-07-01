# textTovoz

Python + Jupyter notebooks learning project.

## Quickstart

```bash
pip install -r requirements.txt && jupyter notebook
```

Open `notebooks/tts_pipeline.ipynb`. In Colab, upload `subtitle.txt` when the
notebook asks for it; the notebook saves it to `/content/subtitle.txt`.

## Personal use only / AI-generated audio

This project is for personal and experimental use only. The bundled sample
`subtitle.txt` is third-party content (a transcription of an ASP.NET Core
tutorial video). Do not redistribute the generated audio. Chatterbox applies
built-in PerTh watermarking to all outputs.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install jupyter
jupyter notebook
```

Notebooks go in `notebooks/`.

## Adding Python deps

```bash
pip install <pkg>
pip freeze | grep -v '^\-e' > requirements.txt
```

## Notes

- This is its own git repo (not part of any monorepo).
- See `AGENTS.md` for conventions.

## Verification

```bash
ruff check .
ruff format --check .
pytest -q
pytest -q tests/test_pipeline_smoke.py
python scripts/validate_manifest.py chunks/manifest.jsonl
```

See `AGENTS.md` for more conventions.
