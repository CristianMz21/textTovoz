"""Lightweight TTS wrappers for Chatterbox and local smoke tests.

Targets the ``chatterbox-tts==0.1.7`` PyPI release. That release exposes
``ChatterboxMultilingualTTS.from_pretrained(device)`` (no repo or
``t3_model`` argument — the unified ``ResembleAI/chatterbox`` Hugging
Face repo is hardcoded and only the V2 multilingual checkpoint is
available). The wrapper still accepts ``t3_model`` for forward
compatibility, but 0.1.7 ignores it.

The multilingual V2 model supports 23+ languages including Spanish
(``language_id="es"``), which is the only language_id we need for this
project.

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
    """Thin lazy wrapper around ``ChatterboxMultilingualTTS`` (0.1.7 API).

    0.1.7 only exposes ``from_pretrained(device)`` — it loads the unified
    ``ResembleAI/chatterbox`` repo and the V2 multilingual checkpoint.
    The wrapper accepts ``t3_model`` for forward compatibility (the
    master branch uses it) but does not pass it through to 0.1.7.
    """

    model: _ChatterboxModel
    config: TTSConfig

    @classmethod
    def from_pretrained(
        cls,
        language_id: str,
        device: str,
        *,
        t3_model: str = "v2",  # noqa: ARG003 - kept for forward compat
        config: TTSConfig | None = None,
    ) -> ChatterboxTTS:
        """Load Chatterbox lazily using the 0.1.7 ``from_pretrained`` API.

        ``language_id`` should be a code the multilingual model supports
        (e.g. ``"es"`` for Spanish). The ``t3_model`` argument is
        accepted for forward compatibility but is ignored by 0.1.7.
        """

        from chatterbox.mtl_tts import ChatterboxMultilingualTTS

        effective_config = config or TTSConfig(language_id=language_id)
        model = ChatterboxMultilingualTTS.from_pretrained(device=device)
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
