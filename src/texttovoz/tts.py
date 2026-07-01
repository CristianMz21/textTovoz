"""Lightweight TTS wrappers for Chatterbox and local smoke tests.

Chatterbox parameter ranges verified during exploration:

- ``exaggeration``: practical range 0.0-1.0; default 0.5, with ~0.7 useful for
  more expressive narration when paired with a lower ``cfg_weight``.
- ``cfg_weight``: default 0.5; values around 0.3 may help if speech is too fast.
- ``temperature``: default 0.8 for baseline sampling behavior.
- ``seed``: applied by the pipeline per chunk as ``seed + chunk_id`` when torch is
  available; reproducibility is best-effort because model/runtime kernels may vary.
"""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

from texttovoz.config import TTSConfig

if TYPE_CHECKING:
    from collections.abc import Protocol

    class _ChatterboxModel(Protocol):
        sr: int

        def generate(self, text: str, *, language_id: str, **kwargs: Any) -> Any: ...


def is_available() -> bool:
    """Return whether Chatterbox can be imported without importing it now."""

    return importlib.util.find_spec("chatterbox") is not None


@dataclass(slots=True)
class ChatterboxTTS:
    """Thin lazy wrapper around ``ChatterboxMultilingualTTS``.

    The LatAm Spanish checkpoint is configured through ``model_id`` and expects
    Chatterbox generation calls to use ``language_id="es"``.
    """

    model: _ChatterboxModel
    config: TTSConfig

    @classmethod
    def from_pretrained(
        cls,
        model_id: str,
        language_id: str,
        device: str,
        *,
        config: TTSConfig | None = None,
    ) -> ChatterboxTTS:
        """Load Chatterbox lazily and forward the configured HF model id.

        ``language_id`` should be ``"es"`` for the configured LatAm Spanish model.
        """

        from chatterbox.mtl_tts import ChatterboxMultilingualTTS

        effective_config = config or TTSConfig(model_id=model_id, language_id=language_id)
        model = ChatterboxMultilingualTTS.from_pretrained(model_id, device=device)
        return cls(model=model, config=effective_config)

    def generate(self, text: str) -> tuple[Any, int]:
        """Generate one audio chunk, returning ``(tensor, sample_rate)``."""

        audio = self.model.generate(
            text,
            language_id=self.config.language_id,
            exaggeration=self.config.exaggeration,
            cfg_weight=self.config.cfg_weight,
            temperature=self.config.temperature,
            repetition_penalty=self.config.repetition_penalty,
            min_p=self.config.min_p,
            top_p=self.config.top_p,
        )
        return audio, int(getattr(self.model, "sr", self.config.sample_rate))


@dataclass(slots=True)
class StubTTS:
    """Deterministic one-second silence generator for local tests."""

    config: TTSConfig

    def generate(self, text: str) -> tuple[np.ndarray, int]:
        """Return one second of mono silence at the configured sample rate."""

        _ = text
        return np.zeros(self.config.sample_rate, dtype=np.float32), self.config.sample_rate
