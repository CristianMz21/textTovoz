"""Spanish sentence tokenization with optional spaCy support."""

from __future__ import annotations

import importlib
import re
from functools import lru_cache

from texttovoz.normalize import has_speakable_content

_BOUNDARY_RE = re.compile(r"(?<=[.!?])\s+(?=[¿¡A-ZÁÉÍÓÚÜÑ0-9])")


@lru_cache(maxsize=1)
def _load_spacy_model() -> object | None:
    # Any failure here (missing dep, binary incompatibility, model not
    # downloaded) must fall back to the regex path silently.
    try:
        spacy = importlib.import_module("spacy")
        return spacy.load("es_core_news_sm")
    except Exception:
        return None


def split_sentences(text: str, max_chars: int = 280, use_spacy: bool = True) -> list[str]:
    """Split Spanish prose into speakable sentence units."""

    stripped = text.strip()
    if not stripped:
        return []
    candidates = _spacy_sentences(stripped) if use_spacy else []
    if not candidates:
        candidates = _regex_sentences(stripped)
    sentences: list[str] = []
    for candidate in candidates:
        clean = candidate.strip()
        if not has_speakable_content(clean):
            continue
        if len(clean) <= max_chars:
            sentences.append(clean)
        else:
            sentences.extend(_split_long_unit(clean, max_chars))
    return sentences


def _spacy_sentences(text: str) -> list[str]:
    model = _load_spacy_model()
    if model is None:
        return []
    doc = model(text)
    return [sent.text.strip() for sent in doc.sents]


def _regex_sentences(text: str) -> list[str]:
    return [part.strip() for part in _BOUNDARY_RE.split(text) if part.strip()]


def _split_long_unit(text: str, max_chars: int) -> list[str]:
    from texttovoz.chunk import split_oversized_sentence

    return split_oversized_sentence(text, max_chars=max_chars)
