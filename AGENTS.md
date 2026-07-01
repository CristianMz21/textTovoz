# textTovoz

## Stack

- Python 3.10+
- Jupyter notebooks (`jupyter notebook` or `jupyter lab`)

## Quickstart

```bash
python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt   # create on first run
pip install jupyter

jupyter notebook   # opens browser UI
```

Work lives in `notebooks/*.ipynb`.

## Conventions

- All exploration / work goes in `notebooks/`.
- Real Python packages (when needed) go to `requirements.txt` or
  `pyproject.toml`. Promote a notebook to a module only when logic is stable
  and reused.
- Use `git` normally: `git checkout -b feat/<name>`, push with
  `git push -u origin <branch>`, open PR against `main`.
- This is its own repo — **independent** of the parent `Learning/` monorepo.
  Do not assume any sibling-project conventions apply here.

## Repo

- Public on GitHub: `github.com/CristianMz21/textTovoz`
- Default branch: `main`
- Local git config: `user.email` set to the GitHub `noreply` address so
  commits verify on the account. Adjust locally with
  `git config user.email "<you>@users.noreply.github.com"` if you need a
  different one.

## Workspace context

- Lives at `~/Projectos/Learning/textTovoz/`. The parent `Learning/` is a
  separate git repo with unrelated projects — its conventions and tools do
  not apply here.
- Sister project: `../vozTotex/` (created same day; treat as a separate
  repo unless explicitly paired by the user).
