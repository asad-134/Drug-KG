from __future__ import annotations

from typing import Any

from .text_utils import candidate_terms, clean_text, normalize_key, split_sentences

MAX_SENTENCES_PER_SECTION = 80
MAX_TERMS_PER_SENTENCE = 12


def _first_text(value: Any) -> str:
    if isinstance(value, list) and value:
        first = value[0]
        return clean_text(str(first))
    if isinstance(value, str):
        return clean_text(value)
    return ""


def _all_text(value: Any) -> list[str]:
    if isinstance(value, list):
        return [clean_text(str(v)) for v in value if str(v).strip()]
    if isinstance(value, str) and value.strip():
        return [clean_text(value)]
    return []


def build_drug_row(record: dict[str, Any]) -> dict[str, Any]:
    openfda = record.get("openfda", {}) or {}
    generic_name = _first_text(openfda.get("generic_name"))
    brand_names = _all_text(openfda.get("brand_name"))
    substance_names = _all_text(openfda.get("substance_name"))
    manufacturer = _first_text(openfda.get("manufacturer_name"))
    route = _first_text(openfda.get("route"))

    source_id = record.get("set_id") or record.get("id") or ""
    if not source_id:
        source_id = "missing_source_id"

    fallback_name = generic_name or (brand_names[0] if brand_names else "unknown")

    return {
        "source_id": source_id,
        "record_id": record.get("id", ""),
        "effective_time": record.get("effective_time", ""),
        "generic_name": generic_name,
        "drug_name": fallback_name,
        "brand_names": "|".join(brand_names),
        "substance_names": "|".join(substance_names),
        "manufacturer_name": manufacturer,
        "route": route,
        "version": str(record.get("version", "")),
        "source_shard": record.get("_shard", ""),
        "source": "openfda",
    }


def section_text(record: dict[str, Any], section: str) -> list[str]:
    return _all_text(record.get(section))


def extract_mentions(
    *,
    source_id: str,
    section: str,
    section_text_items: list[str],
    mention_type: str,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for text in section_text_items:
        sentence_count = 0
        for sentence in split_sentences(text):
            sentence_count += 1
            if sentence_count > MAX_SENTENCES_PER_SECTION:
                break

            term_count = 0
            for term in candidate_terms(sentence):
                term_count += 1
                if term_count > MAX_TERMS_PER_SENTENCE:
                    break
                rows.append(
                    {
                        "source_label_id": source_id,
                        "section_name": section,
                        "mention_type": mention_type,
                        "mention_text": term,
                        "mention_key": normalize_key(term),
                        "text_snippet": sentence[:500],
                    }
                )
    return rows
