"""Build the Colab notebook for the TextTovoz TTS pipeline.

This script constructs `notebooks/tts_pipeline.ipynb` with nbformat so the
notebook is deterministic and remains valid Jupyter Notebook 7+ JSON.
"""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_PATH = ROOT / "notebooks" / "tts_pipeline.ipynb"


def code(source: str) -> str:
    """Return a normalized code cell source string."""

    return dedent(source).strip()


def build_notebook() -> nbf.NotebookNode:
    """Return the deterministic Colab notebook document."""

    notebook = nbf.v4.new_notebook()
    notebook["metadata"] = {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {"name": "python", "pygments_lexer": "ipython3"},
    }
    notebook["cells"] = [
        nbf.v4.new_markdown_cell(
            "# TextTovoz TTS Pipeline (v3.0 — robust install)\n\n"
            "**Personal use only. AI-generated audio. Do not redistribute.**\n\n"
            "_If you do not see the `(v3.0 — robust install)` marker above, "
            "your Colab tab is serving a cached older revision. Hard-refresh "
            "the browser (Ctrl+Shift+R) and reopen the notebook, or use "
            "File > Open notebook > GitHub to force a fresh fetch._"
        ),
        nbf.v4.new_code_cell(
            code(
                """
                import importlib
                import importlib.util
                import logging
                import os
                import shutil
                import subprocess
                import sys
                from pathlib import Path

                logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(message)s")
                logger = logging.getLogger("texttovoz.notebook")

                min_python = (3, 10)
                if sys.version_info[:2] < min_python:
                    logger.error(
                        "Python 3.10+ is required. Runtime is %s",
                        sys.version.split()[0],
                    )
                    raise RuntimeError("Python 3.10+ is required for TextTovoz.")

                # 1. Clone the texttovoz repo so the local package can be imported.
                #    Pin the branch that contains the pipeline implementation.
                #    After the PR is merged to main, change REPO_BRANCH to "main".
                REPO_URL = "https://github.com/CristianMz21/textTovoz.git"
                REPO_BRANCH = "main"
                REPO_DIR = Path("/content/textTovoz")

                def _clone_repo() -> None:
                    if REPO_DIR.exists():
                        logger.info("Removing stale %s", REPO_DIR)
                        shutil.rmtree(REPO_DIR)
                    logger.info("Cloning %s @ %s into %s", REPO_URL, REPO_BRANCH, REPO_DIR)
                    subprocess.check_call(
                        [
                            "git",
                            "clone",
                            "--depth=1",
                            "-b",
                            REPO_BRANCH,
                            REPO_URL,
                            str(REPO_DIR),
                        ]
                    )

                # Ensure a fresh, complete clone every run. Reusing a partial
                # clone is the most common cause of the
                # 'texttovoz package not importable' failure.
                required_paths = [
                    REPO_DIR / "src" / "texttovoz" / "__init__.py",
                    REPO_DIR / "src" / "texttovoz" / "tts.py",
                    REPO_DIR / "src" / "texttovoz" / "pipeline.py",
                    REPO_DIR / "pyproject.toml",
                ]
                if not all(p.exists() for p in required_paths):
                    _clone_repo()
                else:
                    logger.info("Reusing existing clone at %s", REPO_DIR)

                # Last-chance verification: list the directory and bail with a
                # clear error if the expected files are still missing.
                missing = [str(p) for p in required_paths if not p.exists()]
                if missing:
                    ls = subprocess.check_output(
                        ["ls", "-la", str(REPO_DIR / "src" / "texttovoz")]
                    ).decode("utf-8", errors="replace")
                    raise RuntimeError(
                        "texttovoz clone is incomplete. Missing:\\n  "
                        + "\\n  ".join(missing)
                        + "\\nRepo contents:\\n"
                        + ls
                    )

                # 2. Aggressively wipe any stale texttovoz caches that may shadow
                #    the freshly cloned source. This guards against the
                #    'IndentationError on line 45' failure mode that happens
                #    when a partial prior install leaves a corrupt tokenize.py
                #    in site-packages.
                import glob

                for pycache in glob.glob(
                    str(REPO_DIR / "**" / "__pycache__"), recursive=True
                ):
                    shutil.rmtree(pycache, ignore_errors=True)
                for pyc in glob.glob(str(REPO_DIR / "**" / "*.pyc"), recursive=True):
                    try:
                        os.remove(pyc)
                    except OSError:
                        pass

                subprocess.run(
                    [sys.executable, "-m", "pip", "uninstall", "-y", "texttovoz"],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

                # 3. Install Colab runtime dependencies. We do this BEFORE the
                #    editable install so pip can resolve chatterbox-tts first
                #    (it pulls torch/torchaudio/transformers as transitives).
                packages = [
                    "chatterbox-tts==0.1.7",
                    "torch",
                    "torchaudio",
                    "huggingface_hub",
                    "numpy",
                    "soundfile",
                    "pydantic",
                    "pyyaml",
                    "tqdm",
                    "ipython",
                ]
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", *packages]
                )

                # 4. Install the local package editable, using `cwd` and `.` to
                #    avoid absolute-path edge cases. Done last so chatterbox-tts
                #    is resolved before our own package overlays site-packages.
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", "--no-cache-dir", "-e", "."],
                    cwd=str(REPO_DIR),
                )

                # 4. Verify the local package is importable. We do NOT raise here — Cell 2
                #    has its own self-healing install path and will repair any
                #    residual problem with the package.
                importlib.invalidate_caches()
                # Belt-and-suspenders: add the source dir to sys.path directly
                # so the package is importable even if the editable-install .pth
                # file generated by pip is not consulted by this kernel.
                src_path = str(REPO_DIR / "src")
                if src_path not in sys.path:
                    sys.path.insert(0, src_path)
                importlib.invalidate_caches()
                tv_spec = importlib.util.find_spec("texttovoz")
                if tv_spec is None:
                    show = subprocess.run(
                        [sys.executable, "-m", "pip", "show", "-f", "texttovoz"],
                        capture_output=True,
                        text=True,
                    )
                    logger.warning(
                        "texttovoz package not yet importable after editable install; "
                        "Cell 2 will attempt a self-heal.\\n"
                        "pip show -f output:\\n%s\\n%s",
                        show.stdout,
                        show.stderr,
                    )
                else:
                    logger.info("texttovoz package location: %s", tv_spec.origin)

                torch = importlib.import_module("torch")
                if not torch.cuda.is_available():
                    logger.error("No GPU detected. In Colab, choose a T4 GPU runtime.")
                    raise RuntimeError("A CUDA GPU is required for Chatterbox TTS.")

                logger.info(
                    "Dependency check passed with Python %s and GPU %s",
                    sys.version.split()[0],
                    torch.cuda.get_device_name(0),
                )
                """
            )
        ),
        nbf.v4.new_code_cell(
            code(
                """
                import importlib
                import importlib.util
                import os
                import subprocess
                import sys
                from pathlib import Path

                os.environ["HF_HOME"] = "/content/.cache/huggingface"
                model_id = "ResembleAI/Chatterbox-Multilingual-es-mx-latam"

                # Self-heal: if the package is not importable (stale Colab cache
                # or older notebook revision), clone + editable-install the repo
                # right here. This makes the cell robust on its own.
                if importlib.util.find_spec("texttovoz") is None:
                    REPO_URL = "https://github.com/CristianMz21/textTovoz.git"
                    REPO_BRANCH = "main"
                    REPO_DIR = Path("/content/textTovoz")
                    if not (REPO_DIR / "src" / "texttovoz" / "__init__.py").exists():
                        logger.info(
                            "Cloning %s @ %s into %s", REPO_URL, REPO_BRANCH, REPO_DIR
                        )
                        subprocess.check_call(
                            [
                                "git",
                                "clone",
                                "--depth=1",
                                "-b",
                                REPO_BRANCH,
                                REPO_URL,
                                str(REPO_DIR),
                            ]
                        )
                    else:
                        logger.info("Reusing existing clone at %s", REPO_DIR)
                    subprocess.check_call(
                        [sys.executable, "-m", "pip", "install", "-e", str(REPO_DIR)]
                    )
                    importlib.invalidate_caches()
                    # Belt-and-suspenders: also add the source dir to sys.path
                    # directly. In some Colab runtimes the editable-install
                    # .pth file is generated but not consulted by importlib;
                    # this guarantees the package is reachable.
                    src_path = str(REPO_DIR / "src")
                    if src_path not in sys.path:
                        sys.path.insert(0, src_path)
                    importlib.invalidate_caches()
                    tv_spec = importlib.util.find_spec("texttovoz")
                    if tv_spec is None:
                        show = subprocess.run(
                            [
                                sys.executable,
                                "-m",
                                "pip",
                                "show",
                                "-f",
                                "texttovoz",
                            ],
                            capture_output=True,
                            text=True,
                        )
                        raise RuntimeError(
                            "texttovoz package still not importable after pip install -e.\\n"
                            f"sys.path[0:5]: {sys.path[:5]}\\n"
                            f"pip show -f output:\\n{show.stdout}\\n{show.stderr}"
                        )
                    logger.info("texttovoz package location: %s", tv_spec.origin)
                else:
                    logger.info("texttovoz package already importable.")

                if importlib.util.find_spec("huggingface_hub") is None:
                    logger.warning(
                        "huggingface_hub not importable; installing it before model download."
                    )
                    subprocess.check_call(
                        [sys.executable, "-m", "pip", "install", "huggingface_hub"]
                    )
                    importlib.invalidate_caches()

                hf_hub = importlib.import_module("huggingface_hub")
                logger.info("Pre-warming Hugging Face cache at %s", os.environ["HF_HOME"])
                hf_hub.snapshot_download(repo_id=model_id)

                tts_module = importlib.import_module("texttovoz.tts")
                if not tts_module.is_available():
                    raise RuntimeError("Chatterbox import check failed after installation.")
                logger.info("Hugging Face cache and Chatterbox import check completed.")
                """
            )
        ),
        nbf.v4.new_code_cell(
            code(
                """
                from pathlib import Path

                from texttovoz import config, manifest, pipeline

                cfg = config.TTSConfig(
                    input_path=Path("/content/subtitle.txt"),
                    chunks_dir=Path("/content/out/chunks"),
                    output_dir=Path("/content/out"),
                    manifest_path=Path("/content/out/chunks/manifest.jsonl"),
                    output_wav_path=Path("/content/out/full.wav"),
                    language_id="es",
                )
                logger.info(
                    "Configured TextTovoz with manifest schema %s",
                    manifest.ChunkRecord.__name__,
                )
                cfg
                """
            )
        ),
        nbf.v4.new_markdown_cell(
            "## Upload transcript\n\n"
            "Upload a file named `subtitle.txt`; it will be saved to "
            "`/content/subtitle.txt`."
        ),
        nbf.v4.new_code_cell(
            code(
                """
                from google.colab import files

                uploaded = files.upload()
                if not uploaded:
                    raise RuntimeError("Upload was cancelled or produced no files.")

                # Colab may rename a re-uploaded file (e.g. 'subtitle (1).txt'),
                # so accept any *.txt or matching prefix.
                candidates = [k for k in uploaded if k.lower().endswith(".txt")]
                if not candidates:
                    raise RuntimeError(
                        f"Please upload a .txt file. Got: {list(uploaded)}"
                    )
                chosen = next(
                    (k for k in candidates if "subtitle" in k.lower()), candidates[0]
                )
                logger.info("Using uploaded file: %s", chosen)
                Path("/content/subtitle.txt").write_bytes(uploaded[chosen])
                logger.info("Saved transcript to /content/subtitle.txt")
                """
            )
        ),
        nbf.v4.new_code_cell(
            code(
                """
                from dataclasses import replace

                from IPython.display import Audio, display

                preview_cfg = replace(
                    cfg,
                    output_dir=Path("/content/out/preview"),
                    chunks_dir=Path("/content/out/preview/chunks"),
                    manifest_path=Path("/content/out/preview/chunks/manifest.jsonl"),
                    output_wav_path=Path("/content/out/preview/full.wav"),
                    to_chunk=2,
                )
                logger.info(
                    "Generating the first %s chunks for a prosody preview.",
                    preview_cfg.to_chunk,
                )
                preview_result = pipeline.run(preview_cfg)
                logger.info(
                    "Preview generated=%s skipped=%s errors=%s",
                    preview_result.generated,
                    preview_result.skipped,
                    preview_result.errors,
                )
                display(Audio(str(preview_result.output_wav_path)))
                """
            )
        ),
        nbf.v4.new_code_cell(
            code(
                """
                import tqdm

                logger.info("Starting full TextTovoz run; package logs chunk progress.")
                with tqdm.tqdm(total=1, desc="TextTovoz full pipeline") as progress:
                    result = pipeline.run(cfg)
                    progress.update(1)

                logger.info(
                    "Full run complete: total=%s selected=%s generated=%s skipped=%s errors=%s",
                    result.chunks_total,
                    result.chunks_selected,
                    result.generated,
                    result.skipped,
                    result.errors,
                )
                result
                """
            )
        ),
        nbf.v4.new_code_cell(
            code(
                """
                final_wav = Path("/content/out/full.wav")
                if not final_wav.exists():
                    raise FileNotFoundError("Expected final WAV at /content/out/full.wav")

                logger.info("Final WAV ready at %s", final_wav)
                display(Audio("/content/out/full.wav"))
                """
            )
        ),
        nbf.v4.new_markdown_cell(
            "---\n\n**Personal use only. AI-generated audio. Do not redistribute generated audio.**"
        ),
    ]
    return notebook


def main() -> None:
    """Write the notebook to disk."""

    NOTEBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)
    nbf.write(build_notebook(), NOTEBOOK_PATH)


if __name__ == "__main__":
    main()
