from __future__ import annotations

import re
import unicodedata
from hashlib import sha1

_WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9\-']+")
_SPLIT_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
_MULTI_SPACE_RE = re.compile(r"\s+")

STOPWORDS = {
    "and",
    "or",
    "with",
    "without",
    "for",
    "the",
    "this",
    "that",
    "from",
    "into",
    "about",
    "used",
    "use",
    "including",
    "may",
    "patients",
    "patient",
    "capsules",
    "tablet",
    "tablets",
    "injection",
}


def normalize_whitespace(text: str) -> str:
    return _MULTI_SPACE_RE.sub(" ", text).strip()


def clean_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text)
    return normalize_whitespace(normalized)


def normalize_key(text: str) -> str:
    text = clean_text(text).lower()
    text = re.sub(r"[^a-z0-9\s\-]", "", text)
    text = normalize_whitespace(text)
    return text


def stable_id(prefix: str, value: str) -> str:
    digest = sha1(normalize_key(value).encode("utf-8")).hexdigest()[:12]
    return f"{prefix}_{digest}"


def split_sentences(text: str) -> list[str]:
    cleaned = clean_text(text)
    if not cleaned:
        return []
    parts = _SPLIT_SENTENCE_RE.split(cleaned)
    return [p.strip() for p in parts if p.strip()]


def candidate_terms(text: str, max_words: int = 5) -> list[str]:
    tokens = _WORD_RE.findall(text)
    if not tokens:
        return []

    terms: list[str] = []
    window: list[str] = []
    for token in tokens:
        t = token.lower()
        if t in STOPWORDS:
            if 1 <= len(window) <= max_words:
                terms.append(" ".join(window))
            window = []
            continue
        window.append(token)
        if len(window) > max_words:
            window.pop(0)

    if 1 <= len(window) <= max_words:
        terms.append(" ".join(window))

    deduped: list[str] = []
    seen: set[str] = set()
    for term in terms:
        key = normalize_key(term)
        if len(key) < 4:
            continue
        if key not in seen:
            seen.add(key)
            deduped.append(term)
    return deduped
