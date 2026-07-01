# textTovoz

Python + Jupyter notebooks learning project.

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
