"""Text normalization and acronym expansion."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import yaml

_WHITESPACE_RE = re.compile(r"\s+")
_SPEAKABLE_RE = re.compile(r"[\wÁÉÍÓÚÜÑáéíóúüñ]", re.UNICODE)


def load_glossary(path: str | Path) -> dict[str, str]:
    """Load acronym pronunciation mappings from a YAML file."""

    glossary_path = Path(path)
    raw = yaml.safe_load(glossary_path.read_text(encoding="utf-8"))
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ValueError("glossary YAML must contain a mapping")
    glossary: dict[str, str] = {}
    for key, value in raw.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise ValueError("glossary keys and values must be strings")
        glossary[key] = value
    return glossary


def has_speakable_content(text: str) -> bool:
    """Return whether text contains letters or digits worth sending to TTS."""

    return bool(_SPEAKABLE_RE.search(text))


def normalize(text: str, glossary: dict[str, str] | None = None) -> str:
    """Normalize whitespace/control chars and expand configured acronyms."""

    normalized = unicodedata.normalize("NFC", text)
    normalized = "".join(ch for ch in normalized if ch.isprintable() or ch.isspace())
    normalized = _WHITESPACE_RE.sub(" ", normalized).strip()
    if glossary:
        normalized = _expand_glossary(normalized, glossary)
    return normalized


def _expand_glossary(text: str, glossary: dict[str, str]) -> str:
    if not glossary:
        return text
    terms = sorted(glossary, key=len, reverse=True)
    pattern = re.compile(
        r"(?<![\w.])(" + "|".join(re.escape(term) for term in terms) + r")(?![\w.])"
    )
    return pattern.sub(lambda match: glossary[match.group(1)], text)
