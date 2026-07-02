from __future__ import annotations

import sys
import types

from texttovoz.config import TTSConfig
from texttovoz.tts import ChatterboxTTS, StubTTS


def test_stub_tts_returns_one_second_of_silence(stub_config: TTSConfig) -> None:
    audio, sample_rate = StubTTS(stub_config).generate("Hola")

    assert sample_rate == stub_config.sample_rate
    assert len(audio) == stub_config.sample_rate


def test_chatterbox_from_pretrained_forwards_t3_model(monkeypatch) -> None:
    calls: dict[str, object] = {}

    class FakeChatterboxMultilingualTTS:
        sr = 24_000

        @classmethod
        def from_pretrained(cls, *, device: str, t3_model: str | None = None):
            calls["device"] = device
            calls["t3_model"] = t3_model
            return cls()

        def generate(self, text: str, *, language_id: str, **kwargs):
            calls["language_id"] = language_id
            return text, kwargs

    chatterbox_module = types.ModuleType("chatterbox")
    mtl_tts_module = types.ModuleType("chatterbox.mtl_tts")
    mtl_tts_module.ChatterboxMultilingualTTS = FakeChatterboxMultilingualTTS
    monkeypatch.setitem(sys.modules, "chatterbox", chatterbox_module)
    monkeypatch.setitem(sys.modules, "chatterbox.mtl_tts", mtl_tts_module)

    config = TTSConfig(t3_model="v3", language_id="es")
    tts = ChatterboxTTS.from_pretrained("es", "cuda", t3_model="v3", config=config)
    tts.generate("Hola")

    assert calls["device"] == "cuda"
    assert calls["t3_model"] == "v3"
    assert calls["language_id"] == "es"
