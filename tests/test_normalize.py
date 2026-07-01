from __future__ import annotations

import pytest

from texttovoz.normalize import has_speakable_content, load_glossary, normalize


def test_load_glossary_reads_yaml(glossary_file, sample_glossary) -> None:
    assert load_glossary(glossary_file) == sample_glossary


def test_normalize_expands_acronyms_and_preserves_spanish_punctuation(sample_glossary) -> None:
    text = "  ¿ASP.NET usa API?\n¡HTTP también!  "

    result = normalize(text, sample_glossary)

    assert result == "¿A-S-P punto N-E-T usa A-P-I? ¡H-T-T-P también!"


def test_longest_match_expands_asp_net_before_shorter_terms() -> None:
    result = normalize("ASP.NET y NET", {"ASP.NET": "A-S-P punto N-E-T", "NET": "net"})

    assert result == "A-S-P punto N-E-T y net"


def test_non_printable_and_whitespace_are_collapsed(sample_glossary) -> None:
    result = normalize("API\x00\tcon\nacentos: canción", sample_glossary)

    assert result == "A-P-I con acentos: canción"


@pytest.mark.parametrize("text, expected", [("¿?!", False), ("... API", True), ("¡hola!", True)])
def test_has_speakable_content_rejects_punctuation_only(text: str, expected: bool) -> None:
    assert has_speakable_content(text) is expected
