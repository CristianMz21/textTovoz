from __future__ import annotations

import numpy as np

from texttovoz.audio_io import concat_with_silence, load_wav, save_wav


def test_wav_round_trip_preserves_shape_and_rate(tmp_path, sample_audio) -> None:
    path = tmp_path / "chunk.wav"

    save_wav(path, sample_audio, sample_rate=24_000)
    loaded, rate = load_wav(path)

    assert rate == 24_000
    assert loaded.shape == sample_audio.shape
    assert np.allclose(loaded, sample_audio, atol=1e-4)


def test_concat_with_silence_inserts_gap(tmp_path) -> None:
    first = tmp_path / "first.wav"
    second = tmp_path / "second.wav"
    output = tmp_path / "full.wav"
    save_wav(first, np.ones(10, dtype=np.float32), sample_rate=100)
    save_wav(second, np.ones(5, dtype=np.float32), sample_rate=100)

    combined = concat_with_silence([first, second], output, sample_rate=100, silence_ms=100)
    reloaded, rate = load_wav(output)

    assert rate == 100
    assert combined.shape == (25,)
    assert np.allclose(combined[10:20], np.zeros(10, dtype=np.float32))
    assert reloaded.shape == combined.shape
