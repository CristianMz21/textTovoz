from __future__ import annotations

import sys
import types

from texttovoz.config import TTSConfig
from texttovoz.tts import ChatterboxTTS, StubTTS


def test_stub_tts_returns_one_second_of_silence(stub_config: TTSConfig) -> None:
    audio, sample_rate = StubTTS(stub_config).generate("Hola")

    assert sample_rate == stub_config.sample_rate
    assert len(audio) == stub_config.sample_rate


def test_chatterbox_from_pretrained_forwards_device(monkeypatch) -> None:
    calls: dict[str, object] = {}

    class FakeChatterboxMultilingualTTS:
        sr = 24_000

        @classmethod
        def from_pretrained(cls, device: str):
            calls["device"] = device
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
    # t3_model is accepted for forward compat but the 0.1.7 from_pretrained
    # signature only takes device, so the wrapper must NOT pass it through.
    tts = ChatterboxTTS.from_pretrained("es", "cuda", t3_model="v3", config=config)
    tts.generate("Hola")

    assert calls["device"] == "cuda"
    assert "t3_model" not in calls  # 0.1.7 does not accept it
    assert calls["language_id"] == "es"
