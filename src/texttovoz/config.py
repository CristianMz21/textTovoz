"""Configuration defaults for the TextTovoz TTS pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class TTSConfig:
    """Runtime configuration shared by notebooks and modules."""

    input_path: Path = Path("/home/mackroph/Descargas/subtitle.txt")
    chunks_dir: Path = Path("chunks")
    output_dir: Path = Path("output")
    manifest_path: Path = Path("chunks/manifest.jsonl")
    output_wav_path: Path = Path("output/full.wav")
    glossary_path: Path = Path(__file__).with_name("data") / "acronyms.yaml"
    hf_home: Path = Path("/content/.cache/huggingface")
    model_id: str = "ResembleAI/Chatterbox-Multilingual-es-mx-latam"
    language_id: str = "es"
    sample_rate: int = 24_000
    channels: int = 1
    max_chars: int = 280
    silence_gap_ms: int = 100
    seed: int = 42
    exaggeration: float = 0.5
    cfg_weight: float = 0.5
    temperature: float = 0.8
    repetition_penalty: float = 1.2
    min_p: float = 0.05
    top_p: float = 1.0
    watermark_present: bool = True
    refuse_manifest_collision: bool = True
    preview_chunks: int = 2
    from_chunk: int | None = None
    to_chunk: int | None = None

    def __post_init__(self) -> None:
        if self.max_chars <= 0:
            raise ValueError("max_chars must be positive")
        if self.sample_rate <= 0:
            raise ValueError("sample_rate must be positive")
        if self.channels != 1:
            raise ValueError("only mono output is supported")
        if not self.watermark_present:
            raise ValueError("Chatterbox watermarking must remain declared")
        if self.from_chunk is not None and self.from_chunk < 1:
            raise ValueError("from_chunk must be at least 1")
        if self.to_chunk is not None and self.to_chunk < 1:
            raise ValueError("to_chunk must be at least 1")
        if (
            self.from_chunk is not None
            and self.to_chunk is not None
            and self.from_chunk > self.to_chunk
        ):
            raise ValueError("from_chunk must be less than or equal to to_chunk")
