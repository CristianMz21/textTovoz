from __future__ import annotations

from texttovoz.chunk import chunk_sentences, split_oversized_sentence


def test_chunks_group_sentences_without_exceeding_cap() -> None:
    sentences = ["Primera oración.", "Segunda oración breve.", "Tercera."]

    result = chunk_sentences(sentences, max_chars=40)

    assert result == ["Primera oración. Segunda oración breve.", "Tercera."]
    assert all(len(chunk) <= 40 for chunk in result)


def test_chunking_preserves_sentence_boundaries_after_tokenization() -> None:
    sentences = ["Uno.", "Dos.", "Tres."]

    result = chunk_sentences(sentences, max_chars=9)

    assert result == ["Uno. Dos.", "Tres."]


def test_clause_split_prefers_commas_and_conjunctions() -> None:
    sentence = "Este tramo es largo, contiene una pausa útil y termina con una idea clara."

    result = split_oversized_sentence(sentence, max_chars=34)

    assert result == [
        "Este tramo es largo,",
        "contiene una pausa útil",
        "y termina con una idea clara.",
    ]


def test_hard_split_handles_long_word() -> None:
    result = split_oversized_sentence("supercalifragilistico", max_chars=8)

    assert result == ["supercal", "ifragili", "stico"]
