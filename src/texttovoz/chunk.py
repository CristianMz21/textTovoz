"""Sentence-aware chunking for TTS generation."""

from __future__ import annotations

import re

from texttovoz.normalize import has_speakable_content

_CLAUSE_RE = re.compile(
    r"(?<=[,;:])\s+|\s+(?=(?:y|o|pero|porque|aunque|entonces)\b)",
    re.IGNORECASE,
)


def chunk_sentences(sentences: list[str], max_chars: int = 280) -> list[str]:
    """Group pre-tokenized sentences into chunks no longer than *max_chars*."""

    if max_chars <= 0:
        raise ValueError("max_chars must be positive")
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        for unit in _ensure_within_cap(sentence.strip(), max_chars):
            if not has_speakable_content(unit):
                continue
            candidate = f"{current} {unit}".strip() if current else unit
            if len(candidate) <= max_chars:
                current = candidate
                continue
            if current:
                chunks.append(current)
            current = unit
    if current:
        chunks.append(current)
    return chunks


def split_oversized_sentence(sentence: str, max_chars: int = 280) -> list[str]:
    """Split one long sentence at clause boundaries, then hard-split if needed."""

    if max_chars <= 0:
        raise ValueError("max_chars must be positive")
    parts = [part.strip() for part in _CLAUSE_RE.split(sentence) if part.strip()]
    if len(parts) == 1:
        return _hard_split(sentence, max_chars)
    units: list[str] = []
    current = ""
    for part in parts:
        candidate = f"{current} {part}".strip() if current else part
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            units.extend(_hard_split(current, max_chars))
        current = part
    if current:
        units.extend(_hard_split(current, max_chars))
    return units


def _ensure_within_cap(sentence: str, max_chars: int) -> list[str]:
    if len(sentence) <= max_chars:
        return [sentence]
    return split_oversized_sentence(sentence, max_chars=max_chars)


def _hard_split(text: str, max_chars: int) -> list[str]:
    words = text.split()
    chunks: list[str] = []
    current = ""
    for word in words:
        if len(word) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(word[i : i + max_chars] for i in range(0, len(word), max_chars))
            continue
        candidate = f"{current} {word}".strip() if current else word
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            chunks.append(current)
        current = word
    if current:
        chunks.append(current)
    return chunks
