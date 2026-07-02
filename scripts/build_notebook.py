"""Build the Colab notebook for the TextTovoz TTS pipeline.

The notebook is structured like a professional script:

  Cell 1  pip install (runtime dependencies)
  Cell 2  git clone + pip install -e (local texttovoz package)
  Cell 3  import statements
  Cell 4  configuration (paths, model id, language id)
  Cell 5  environment verification (Python, GPU, package)
  Cell 6  Hugging Face cache pre-warm
  Cell 7  markdown: "Upload transcript"
  Cell 8  upload widget
  Cell 9  preview (first 2 chunks)
  Cell 10 full run
  Cell 11 export and inline audio playback
  Cell 12 markdown: disclaimer

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
        # ------------------------------------------------------------------
        # Title
        # ------------------------------------------------------------------
        nbf.v4.new_markdown_cell(
            "# TextTovoz TTS Pipeline (v3.1 — install/setup/exec split)\n\n"
            "**Personal use only. AI-generated audio. Do not redistribute.**\n\n"
            "_If you do not see the `(v3.1)` marker above, your Colab tab is "
            "serving a cached older revision. Hard-refresh the browser "
            "(Ctrl+Shift+R) and reopen the notebook._"
        ),
        # ------------------------------------------------------------------
        # Cell 1 — pip install (runtime dependencies only)
        # ------------------------------------------------------------------
        nbf.v4.new_code_cell(
            code(
                """
                # Cell 1: install runtime dependencies via pip.
                # No logic, no imports, no config — strictly package installation.
                # This mirrors the convention of a professional Python script:
                # requirements are declared and installed up front.
                #
                # Colab's base image pre-installs a torch/torchvision pair that
                # is often out of sync with the rest of the ML stack. Uninstall
                # them first, then pin a known-compatible set (torch 2.6.0,
                # torchvision 0.21.0, torchaudio 2.6.0) before installing
                # chatterbox-tts, which depends on all four.
                !pip install -q --upgrade pip
                !pip uninstall -y -q torch torchvision torchaudio transformers
                !pip install -q torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0
                !pip install -q transformers==5.2.0
                !pip install -q chatterbox-tts==0.1.7
                !pip install -q huggingface_hub soundfile
                !pip install -q 'pydantic>=2' pyyaml tqdm ipython
                """
            )
        ),
        # ------------------------------------------------------------------
        # Cell 2 — clone the local repo and install the texttovoz package
        # ------------------------------------------------------------------
        nbf.v4.new_code_cell(
            code(
                """
                # Cell 2: clone the textTovoz repo and pip install the local
                # package editable. Runs after Cell 1 so chatterbox-tts is
                # already on the system.
                import shutil
                import subprocess
                import sys
                from pathlib import Path

                REPO_URL = "https://github.com/CristianMz21/textTovoz.git"
                REPO_BRANCH = "main"
                REPO_DIR = Path("/content/textTovoz")

                # Always wipe any prior clone to guarantee fresh source.
                if REPO_DIR.exists():
                    shutil.rmtree(REPO_DIR)
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

                # Editable install of the local package.
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", "--no-cache-dir", "-e", "."],
                    cwd=str(REPO_DIR),
                )

                # Belt-and-suspenders: add src/ to sys.path directly. Some
                # Colab runtimes do not consult the editable-install .pth file.
                src_path = str(REPO_DIR / "src")
                if src_path not in sys.path:
                    sys.path.insert(0, src_path)
                """
            )
        ),
        # ------------------------------------------------------------------
        # Cell 3 — imports (project + stdlib)
        # ------------------------------------------------------------------
        nbf.v4.new_code_cell(
            code(
                """
                # Cell 3: imports. Stdlib first, then third-party, then local.
                import logging
                import os
                import sys
                from dataclasses import replace
                from pathlib import Path

                from huggingface_hub import snapshot_download
                from IPython.display import Audio, display

                from texttovoz import config, manifest, pipeline
                from texttovoz.config import TTSConfig

                logging.basicConfig(
                    level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
                )
                logger = logging.getLogger("texttovoz.notebook")
                """
            )
        ),
        # ------------------------------------------------------------------
        # Cell 4 — configuration
        # ------------------------------------------------------------------
        nbf.v4.new_code_cell(
            code(
                """
                # Cell 4: configuration constants and TTSConfig instance.
                HF_HOME = "/content/.cache/huggingface"
                os.environ["HF_HOME"] = HF_HOME

                MODEL_ID = "ResembleAI/Chatterbox-Multilingual-es-mx-latam"
                LANGUAGE_ID = "es"

                INPUT_PATH = Path("/content/subtitle.txt")
                OUTPUT_DIR = Path("/content/out")
                CHUNKS_DIR = OUTPUT_DIR / "chunks"
                MANIFEST_PATH = CHUNKS_DIR / "manifest.jsonl"
                OUTPUT_WAV_PATH = OUTPUT_DIR / "full.wav"

                cfg = TTSConfig(
                    input_path=INPUT_PATH,
                    chunks_dir=CHUNKS_DIR,
                    output_dir=OUTPUT_DIR,
                    manifest_path=MANIFEST_PATH,
                    output_wav_path=OUTPUT_WAV_PATH,
                    language_id=LANGUAGE_ID,
                    model_id=MODEL_ID,
                )
                logger.info("Config: model=%s language=%s", cfg.model_id, cfg.language_id)
                cfg
                """
            )
        ),
        # ------------------------------------------------------------------
        # Cell 5 — environment verification
        # ------------------------------------------------------------------
        nbf.v4.new_code_cell(
            code(
                """
                # Cell 5: verify Python, GPU, and that the local package is reachable.
                import importlib.util

                import torch

                if sys.version_info[:2] < (3, 10):
                    raise RuntimeError(
                        f"Python 3.10+ required. Runtime is {sys.version.split()[0]}."
                    )
                if not torch.cuda.is_available():
                    raise RuntimeError(
                        "No CUDA GPU detected. In Colab: "
                        "Runtime > Change runtime type > T4 GPU."
                    )
                tv_spec = importlib.util.find_spec("texttovoz")
                if tv_spec is None:
                    raise RuntimeError(
                        "texttovoz package not importable. Re-run Cells 1 and 2."
                    )

                logger.info("Python %s", sys.version.split()[0])
                logger.info("GPU: %s", torch.cuda.get_device_name(0))
                logger.info("texttovoz at: %s", tv_spec.origin)
                """
            )
        ),
        # ------------------------------------------------------------------
        # Cell 6 — pre-warm Hugging Face cache
        # ------------------------------------------------------------------
        nbf.v4.new_code_cell(
            code(
                """
                # Cell 6: pre-warm the Hugging Face cache so the model weights
                # are on local disk before the first TTS call.
                logger.info("Downloading %s to %s", MODEL_ID, HF_HOME)
                snapshot_download(repo_id=MODEL_ID, cache_dir=HF_HOME)
                logger.info("Model ready.")
                """
            )
        ),
        # ------------------------------------------------------------------
        # Cell 7 — markdown: upload transcript
        # ------------------------------------------------------------------
        nbf.v4.new_markdown_cell(
            "## Upload transcript\n\n"
            "Upload a file named `subtitle.txt` (Colab may rename re-uploads to "
            "`subtitle (1).txt`; the cell accepts any `.txt`)."
        ),
        # ------------------------------------------------------------------
        # Cell 8 — upload widget
        # ------------------------------------------------------------------
        nbf.v4.new_code_cell(
            code(
                """
                # Cell 8: upload widget. Accepts any .txt file and prefers one
                # whose name contains "subtitle" to handle Colab's rename.
                from google.colab import files

                uploaded = files.upload()
                if not uploaded:
                    raise RuntimeError("Upload was cancelled or produced no files.")

                candidates = [k for k in uploaded if k.lower().endswith(".txt")]
                if not candidates:
                    raise RuntimeError(
                        f"Please upload a .txt file. Got: {list(uploaded)}"
                    )
                chosen = next(
                    (k for k in candidates if "subtitle" in k.lower()), candidates[0]
                )
                INPUT_PATH.write_bytes(uploaded[chosen])
                logger.info("Saved transcript: %s (%d bytes)", chosen, len(uploaded[chosen]))
                """
            )
        ),
        # ------------------------------------------------------------------
        # Cell 9 — preview (first 2 chunks)
        # ------------------------------------------------------------------
        nbf.v4.new_code_cell(
            code(
                """
                # Cell 9: generate the first 2 chunks so the user can sanity-check
                # prosody before committing to the full run.
                preview_dir = OUTPUT_DIR / "preview"
                preview_cfg = replace(
                    cfg,
                    chunks_dir=preview_dir / "chunks",
                    output_dir=preview_dir,
                    manifest_path=preview_dir / "chunks" / "manifest.jsonl",
                    output_wav_path=preview_dir / "full.wav",
                    to_chunk=2,
                )
                preview_result = pipeline.run(preview_cfg)
                logger.info(
                    "Preview done: generated=%d skipped=%d errors=%d",
                    preview_result.generated,
                    preview_result.skipped,
                    preview_result.errors,
                )
                display(Audio(str(preview_result.output_wav_path)))
                """
            )
        ),
        # ------------------------------------------------------------------
        # Cell 10 — full run
        # ------------------------------------------------------------------
        nbf.v4.new_code_cell(
            code(
                """
                # Cell 10: full TTS run over every chunk.
                import tqdm

                logger.info("Starting full TextTovoz run.")
                with tqdm.tqdm(total=1, desc="TextTovoz full pipeline") as progress:
                    result = pipeline.run(cfg)
                    progress.update(1)
                logger.info(
                    "Full run complete: total=%d selected=%d generated=%d skipped=%d errors=%d",
                    result.chunks_total,
                    result.chunks_selected,
                    result.generated,
                    result.skipped,
                    result.errors,
                )
                """
            )
        ),
        # ------------------------------------------------------------------
        # Cell 11 — export and inline audio playback
        # ------------------------------------------------------------------
        nbf.v4.new_code_cell(
            code(
                """
                # Cell 11: verify the final WAV exists and play it inline.
                if not OUTPUT_WAV_PATH.exists():
                    raise FileNotFoundError(f"Expected final WAV at {OUTPUT_WAV_PATH}")
                logger.info("Final WAV ready: %s", OUTPUT_WAV_PATH)
                display(Audio(str(OUTPUT_WAV_PATH)))
                """
            )
        ),
        # ------------------------------------------------------------------
        # Cell 12 — disclaimer
        # ------------------------------------------------------------------
        nbf.v4.new_markdown_cell(
            "---\n\n"
            "**Personal use only. AI-generated audio. Do not redistribute "
            "generated audio.**"
        ),
    ]
    return notebook


def main() -> None:
    """Write the notebook to disk."""

    NOTEBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)
    nbf.write(build_notebook(), NOTEBOOK_PATH)


if __name__ == "__main__":
    main()
