from __future__ import annotations

from types import SimpleNamespace

from texttovoz import tokenize


def test_regex_fallback_splits_spanish_sentences() -> None:
    text = "¿Qué es esto? Es una API. ¡Funciona bien!"

    result = tokenize.split_sentences(text, use_spacy=False)

    assert result == ["¿Qué es esto?", "Es una API.", "¡Funciona bien!"]


def test_spacy_path_uses_doc_sents(monkeypatch) -> None:
    sent_a = SimpleNamespace(text="¿Primera oración?")
    sent_b = SimpleNamespace(text="Segunda oración.")
    doc = SimpleNamespace(sents=[sent_a, sent_b])
    monkeypatch.setattr(tokenize, "_load_spacy_model", lambda: lambda text: doc)

    result = tokenize.split_sentences("ignored", use_spacy=True)

    assert result == ["¿Primera oración?", "Segunda oración."]


def test_long_sentence_is_split_to_cap() -> None:
    text = "uno dos tres cuatro cinco seis siete ocho nueve diez once doce."

    result = tokenize.split_sentences(text, max_chars=18, use_spacy=False)

    assert all(len(sentence) <= 18 for sentence in result)
    assert result[:2] == ["uno dos tres", "cuatro cinco seis"]
