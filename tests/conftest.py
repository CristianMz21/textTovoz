from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from texttovoz.config import TTSConfig


@pytest.fixture
def sample_text() -> str:
    return "¿Qué es ASP.NET? Es una API para HTTP. ¡Vamos con una URL!"


@pytest.fixture
def sample_glossary() -> dict[str, str]:
    return {
        "ASP.NET": "A-S-P punto N-E-T",
        "API": "A-P-I",
        "HTTP": "H-T-T-P",
        "URL": "U-R-L",
        "ID": "I-D",
        "JPG": "J-P-G",
    }


@pytest.fixture
def glossary_file(tmp_path: Path, sample_glossary: dict[str, str]) -> Path:
    path = tmp_path / "acronyms.yaml"
    content = "\n".join(f"{key}: {value}" for key, value in sample_glossary.items())
    path.write_text(content, encoding="utf-8")
    return path


@pytest.fixture
def stub_config(tmp_path: Path) -> TTSConfig:
    return TTSConfig(
        input_path=tmp_path / "subtitle.txt",
        chunks_dir=tmp_path / "chunks",
        output_dir=tmp_path / "output",
        manifest_path=tmp_path / "chunks" / "manifest.jsonl",
        output_wav_path=tmp_path / "output" / "full.wav",
        glossary_path=tmp_path / "acronyms.yaml",
    )


@pytest.fixture
def sample_audio() -> np.ndarray:
    return np.linspace(-0.5, 0.5, 2_400, dtype=np.float32)
