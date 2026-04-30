from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .config import Phase2Config

SUSPICIOUS_TERMS = {
    "patient",
    "patients",
    "treatment",
    "therapy",
    "capsule",
    "capsules",
    "tablet",
    "tablets",
    "drug",
    "drugs",
}


@dataclass(slots=True)
class ValidationResult:
    report_path: Path
    suspicious_terms_path: Path


def run_validation(config: Phase2Config) -> ValidationResult:
    graph = config.graph_dir
    validation = config.validation_dir

    drugs = _read_csv(graph / "drugs.csv")
    conditions = _read_csv(graph / "conditions.csv")
    side_effects = _read_csv(graph / "side_effects.csv")
    treats = _read_csv(graph / "treats.csv")
    has_side_effect = _read_csv(graph / "has_side_effect.csv")
    contraindicated_in = _read_csv(graph / "contraindicated_in.csv")
    interacts_with = _read_csv(graph / "interacts_with.csv")
    unresolved = _read_csv(validation / "interaction_unresolved.csv")

    report = {
        "structural": {
            "duplicate_drug_ids": _dup_count(drugs, "drug_id"),
            "duplicate_condition_ids": _dup_count(conditions, "condition_id"),
            "duplicate_side_effect_ids": _dup_count(side_effects, "effect_id"),
            "missing_drug_id": _missing_count(drugs, "drug_id"),
            "missing_condition_id": _missing_count(conditions, "condition_id"),
            "missing_side_effect_id": _missing_count(side_effects, "effect_id"),
        },
        "orphan_relationships": {
            "treats_source_missing": _orphan_count(
                treats, "source_drug_id", set(drugs["drug_id"])
            ),
            "treats_target_missing": _orphan_count(
                treats, "target_condition_id", set(conditions["condition_id"])
            ),
            "has_side_effect_source_missing": _orphan_count(
                has_side_effect, "source_drug_id", set(drugs["drug_id"])
            ),
            "has_side_effect_target_missing": _orphan_count(
                has_side_effect, "target_effect_id", set(side_effects["effect_id"])
            ),
            "contraindicated_in_source_missing": _orphan_count(
                contraindicated_in, "source_drug_id", set(drugs["drug_id"])
            ),
            "contraindicated_in_target_missing": _orphan_count(
                contraindicated_in, "target_condition_id", set(conditions["condition_id"])
            ),
            "interacts_with_source_missing": _orphan_count(
                interacts_with, "source_drug_id", set(drugs["drug_id"])
            ),
            "interacts_with_target_missing": _orphan_count(
                interacts_with, "target_drug_id", set(drugs["drug_id"])
            ),
        },
        "traceability": {
            "treats_missing_provenance": _missing_provenance_count(treats),
            "has_side_effect_missing_provenance": _missing_provenance_count(has_side_effect),
            "contraindicated_in_missing_provenance": _missing_provenance_count(
                contraindicated_in
            ),
            "interacts_with_missing_provenance": _missing_provenance_count(interacts_with),
        },
        "semantic": {
            "suspicious_condition_terms": int(
                conditions[conditions["normalized_name"].isin(SUSPICIOUS_TERMS)].shape[0]
            ),
            "suspicious_side_effect_terms": int(
                side_effects[side_effects["normalized_name"].isin(SUSPICIOUS_TERMS)].shape[0]
            ),
            "unresolved_interaction_mentions": int(len(unresolved)),
        },
    }

    suspicious_conditions = conditions[
        conditions["normalized_name"].isin(SUSPICIOUS_TERMS)
    ].copy()
    suspicious_conditions = suspicious_conditions.assign(
        node_type="Condition", node_id=suspicious_conditions["condition_id"]
    )

    suspicious_side_effects = side_effects[
        side_effects["normalized_name"].isin(SUSPICIOUS_TERMS)
    ].copy()
    suspicious_side_effects = suspicious_side_effects.assign(
        node_type="SideEffect", node_id=suspicious_side_effects["effect_id"]
    )

    suspicious_terms_df = pd.concat(
        [suspicious_conditions, suspicious_side_effects],
        ignore_index=True,
    )

    suspicious_terms_path = validation / "suspicious_terms.csv"
    suspicious_terms_df.to_csv(suspicious_terms_path, index=False)

    report_path = validation / "validation_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    return ValidationResult(report_path=report_path, suspicious_terms_path=suspicious_terms_path)


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False).fillna("")


def _dup_count(df: pd.DataFrame, col: str) -> int:
    if df.empty or col not in df.columns:
        return 0
    return int(df.duplicated(subset=[col]).sum())


def _missing_count(df: pd.DataFrame, col: str) -> int:
    if df.empty or col not in df.columns:
        return 0
    return int((df[col].astype(str).str.strip() == "").sum())


def _orphan_count(df: pd.DataFrame, col: str, valid_ids: set[str]) -> int:
    if df.empty or col not in df.columns:
        return 0
    return int((~df[col].astype(str).isin(valid_ids)).sum())


def _missing_provenance_count(df: pd.DataFrame) -> int:
    if df.empty:
        return 0
    if "source_label_id" not in df.columns or "section_name" not in df.columns:
        return len(df)
    missing_source = df["source_label_id"].astype(str).str.strip() == ""
    missing_section = df["section_name"].astype(str).str.strip() == ""
    return int((missing_source | missing_section).sum())
