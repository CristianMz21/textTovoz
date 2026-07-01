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
            "# TextTovoz TTS Pipeline\n\n"
            "**Personal use only. AI-generated audio. Do not redistribute.**"
        ),
        nbf.v4.new_code_cell(
            code(
                """
                import importlib
                import logging
                import subprocess
                import sys

                logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(message)s")
                logger = logging.getLogger("texttovoz.notebook")

                min_python = (3, 10)
                if sys.version_info[:2] < min_python:
                    logger.error(
                        "Python 3.10+ is required. Runtime is %s",
                        sys.version.split()[0],
                    )
                    raise RuntimeError("Python 3.10+ is required for TextTovoz.")

                packages = [
                    "chatterbox-tts==0.1.7",
                    "torch",
                    "torchaudio",
                    "soundfile",
                    "pydantic",
                    "pyyaml",
                    "tqdm",
                    "ipython",
                ]
                subprocess.check_call([sys.executable, "-m", "pip", "install", *packages])

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
                import os

                os.environ["HF_HOME"] = "/content/.cache/huggingface"
                model_id = "ResembleAI/Chatterbox-Multilingual-es-mx-latam"

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
                if "subtitle.txt" not in uploaded:
                    raise RuntimeError("Please upload a file named subtitle.txt.")

                Path("/content/subtitle.txt").write_bytes(uploaded["subtitle.txt"])
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
