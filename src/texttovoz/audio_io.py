"""WAV read/write and concatenation helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf


def save_wav(path: str | Path, audio: Any, sample_rate: int = 24_000) -> None:
    """Save mono-compatible audio data as WAV."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(output_path, _to_mono_float32(audio), sample_rate, format="WAV")


def load_wav(path: str | Path) -> tuple[np.ndarray, int]:
    """Load a WAV file as mono float32 samples plus sample rate."""

    audio, sample_rate = sf.read(Path(path), dtype="float32", always_2d=False)
    return _to_mono_float32(audio), int(sample_rate)


def concat_with_silence(
    wav_paths: list[str | Path],
    output_path: str | Path,
    *,
    sample_rate: int = 24_000,
    silence_ms: int = 100,
) -> np.ndarray:
    """Concatenate WAV files with a silence gap and persist the result."""

    if silence_ms < 0:
        raise ValueError("silence_ms must be non-negative")
    pieces: list[np.ndarray] = []
    silence = np.zeros(round(sample_rate * silence_ms / 1000), dtype=np.float32)
    for index, wav_path in enumerate(wav_paths):
        audio, loaded_rate = load_wav(wav_path)
        if loaded_rate != sample_rate:
            raise ValueError(f"sample rate mismatch for {wav_path}: {loaded_rate} != {sample_rate}")
        if index:
            pieces.append(silence)
        pieces.append(audio)
    combined = (
        np.concatenate(pieces).astype(np.float32) if pieces else np.array([], dtype=np.float32)
    )
    save_wav(output_path, combined, sample_rate=sample_rate)
    return combined


def _to_mono_float32(audio: Any) -> np.ndarray:
    if hasattr(audio, "detach"):
        audio = audio.detach()
    if hasattr(audio, "cpu"):
        audio = audio.cpu()
    if hasattr(audio, "numpy"):
        audio = audio.numpy()
    array = np.asarray(audio, dtype=np.float32)
    array = np.squeeze(array)
    if array.ndim == 0:
        return array.reshape(1)
    if array.ndim == 1:
        return array
    if array.ndim == 2:
        if 1 in array.shape:
            return array.reshape(-1)
        return array.mean(axis=1).astype(np.float32)
    raise ValueError(f"audio must be mono or stereo-like, got shape {array.shape}")
