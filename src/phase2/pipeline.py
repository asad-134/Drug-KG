from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from phase1.text_utils import normalize_key

from .config import Phase2Config


CONFIDENCE_BY_REL = {
    "TREATS": 0.75,
    "HAS_SIDE_EFFECT": 0.7,
    "CONTRAINDICATED_IN": 0.8,
    "INTERACTS_WITH": 0.65,
}

NOISE_TERMS = {
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
class Phase2Result:
    graph_dir: Path
    validation_dir: Path
    stats_path: Path


def run_phase2(config: Phase2Config) -> Phase2Result:
    config.ensure_dirs()

    drugs_staging = _read_csv(config.staging_dir / "drugs_staging.csv")
    indications_staging = _read_csv(config.staging_dir / "indication_mentions_staging.csv")
    adverse_staging = _read_csv(config.staging_dir / "adverse_effect_mentions_staging.csv")
    contraindication_staging = _read_csv(
        config.staging_dir / "contraindication_mentions_staging.csv"
    )
    interaction_staging = _read_csv(config.staging_dir / "interaction_mentions_staging.csv")

    indications_staging = _filter_noise_mentions(indications_staging)
    adverse_staging = _filter_noise_mentions(adverse_staging)
    contraindication_staging = _filter_noise_mentions(contraindication_staging)
    interaction_staging = _filter_noise_mentions(interaction_staging)

    drugs = build_drug_nodes(drugs_staging)
    conditions = build_condition_nodes(indications_staging, contraindication_staging)
    side_effects = build_side_effect_nodes(adverse_staging)

    treats = build_relationship_table(
        rel_type="TREATS",
        frame=indications_staging,
        source_col="source_label_id",
        target_col="condition_id",
        target_name="target_condition_id",
    )
    has_side_effect = build_relationship_table(
        rel_type="HAS_SIDE_EFFECT",
        frame=adverse_staging,
        source_col="source_label_id",
        target_col="effect_id",
        target_name="target_effect_id",
    )
    contraindicated_in = build_relationship_table(
        rel_type="CONTRAINDICATED_IN",
        frame=contraindication_staging,
        source_col="source_label_id",
        target_col="condition_id",
        target_name="target_condition_id",
    )

    interacts_with, interaction_unresolved = build_interaction_relationships(
        drugs=drugs,
        interaction_staging=interaction_staging,
    )

    _write_csv(config.graph_dir / "drugs.csv", drugs)
    _write_csv(config.graph_dir / "conditions.csv", conditions)
    _write_csv(config.graph_dir / "side_effects.csv", side_effects)
    _write_csv(config.graph_dir / "treats.csv", treats)
    _write_csv(config.graph_dir / "has_side_effect.csv", has_side_effect)
    _write_csv(config.graph_dir / "contraindicated_in.csv", contraindicated_in)
    _write_csv(config.graph_dir / "interacts_with.csv", interacts_with)
    _write_csv(config.validation_dir / "interaction_unresolved.csv", interaction_unresolved)

    stats = {
        "nodes": {
            "drugs": int(len(drugs)),
            "conditions": int(len(conditions)),
            "side_effects": int(len(side_effects)),
        },
        "relationships": {
            "treats": int(len(treats)),
            "has_side_effect": int(len(has_side_effect)),
            "contraindicated_in": int(len(contraindicated_in)),
            "interacts_with": int(len(interacts_with)),
        },
        "interaction_resolution": {
            "resolved": int(len(interacts_with)),
            "unresolved_mentions": int(len(interaction_unresolved)),
        },
    }

    stats_path = config.phase2_output_dir / "phase2_stats.json"
    stats_path.write_text(json.dumps(stats, indent=2), encoding="utf-8")

    return Phase2Result(
        graph_dir=config.graph_dir,
        validation_dir=config.validation_dir,
        stats_path=stats_path,
    )


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing required input CSV: {path}")
    df = pd.read_csv(path, low_memory=False)
    return df.fillna("")


def _write_csv(path: Path, frame: pd.DataFrame) -> None:
    frame.to_csv(path, index=False)


def _filter_noise_mentions(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame

    filtered = frame.copy()
    if "mention_key" in filtered.columns:
        mention_key = filtered["mention_key"].astype(str).str.strip().str.lower()
        filtered = filtered[
            (mention_key != "")
            & (~mention_key.isin(NOISE_TERMS))
            & (mention_key.str.len() >= 3)
            & (~mention_key.str.fullmatch(r"\d+"))
        ]

    return filtered.reset_index(drop=True)


def build_drug_nodes(drugs_staging: pd.DataFrame) -> pd.DataFrame:
    drugs = drugs_staging.copy()
    drugs = drugs.drop_duplicates(subset=["source_id"])
    drugs["drug_id"] = drugs["source_id"].astype(str)
    drugs["normalized_name"] = drugs["generic_name"].astype(str).map(normalize_key)
    fallback = drugs["drug_name"].astype(str).map(normalize_key)
    drugs.loc[drugs["normalized_name"] == "", "normalized_name"] = fallback

    cols = [
        "drug_id",
        "generic_name",
        "drug_name",
        "brand_names",
        "substance_names",
        "manufacturer_name",
        "route",
        "effective_time",
        "version",
        "source",
        "source_id",
        "record_id",
        "source_shard",
        "normalized_name",
    ]
    return drugs[cols].reset_index(drop=True)


def build_condition_nodes(
    indications_staging: pd.DataFrame,
    contraindication_staging: pd.DataFrame,
) -> pd.DataFrame:
    combined = pd.concat(
        [
            indications_staging[["condition_id", "mention_text", "mention_key"]],
            contraindication_staging[["condition_id", "mention_text", "mention_key"]],
        ],
        ignore_index=True,
    )
    combined = combined[combined["condition_id"].astype(str) != ""]

    grouped = (
        combined.groupby("condition_id", as_index=False)
        .agg(
            name=("mention_text", "first"),
            normalized_name=("mention_key", "first"),
            mention_count=("mention_text", "count"),
        )
        .sort_values("mention_count", ascending=False)
    )
    return grouped[["condition_id", "name", "normalized_name", "mention_count"]]


def build_side_effect_nodes(adverse_staging: pd.DataFrame) -> pd.DataFrame:
    effects = adverse_staging[["effect_id", "mention_text", "mention_key"]].copy()
    effects = effects[effects["effect_id"].astype(str) != ""]

    grouped = (
        effects.groupby("effect_id", as_index=False)
        .agg(
            name=("mention_text", "first"),
            normalized_name=("mention_key", "first"),
            mention_count=("mention_text", "count"),
        )
        .sort_values("mention_count", ascending=False)
    )
    return grouped[["effect_id", "name", "normalized_name", "mention_count"]]


def build_relationship_table(
    *,
    rel_type: str,
    frame: pd.DataFrame,
    source_col: str,
    target_col: str,
    target_name: str,
) -> pd.DataFrame:
    rel = frame[
        [target_col, "source_label_id", "section_name", "text_snippet", "mention_key"]
    ].copy()
    rel["source_drug_id"] = frame[source_col].astype(str)
    rel = rel.rename(columns={target_col: target_name})
    rel = rel[(rel["source_drug_id"].astype(str) != "") & (rel[target_name].astype(str) != "")]
    rel["relationship_type"] = rel_type
    rel["confidence_score"] = CONFIDENCE_BY_REL[rel_type]
    rel = rel.drop_duplicates(subset=["source_drug_id", target_name, "section_name", "mention_key"])

    cols = [
        "source_drug_id",
        target_name,
        "relationship_type",
        "source_label_id",
        "section_name",
        "text_snippet",
        "mention_key",
        "confidence_score",
    ]
    return rel[cols].reset_index(drop=True)


def build_interaction_relationships(
    *,
    drugs: pd.DataFrame,
    interaction_staging: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    # Build mention_key -> candidate drug ids map without expanding into a giant join table.
    key_to_ids: dict[str, set[str]] = defaultdict(set)
    key_to_name: dict[str, str] = {}

    for _, row in drugs.iterrows():
        drug_id = str(row["drug_id"])

        candidates: list[str] = []
        candidates.append(str(row.get("generic_name", "")))
        candidates.append(str(row.get("drug_name", "")))
        candidates.extend(str(row.get("brand_names", "")).split("|"))
        candidates.extend(str(row.get("substance_names", "")).split("|"))

        for name in candidates:
            key = normalize_key(name)
            if key:
                key_to_ids[key].add(drug_id)
                # Keep a representative human-readable name for reporting.
                if key not in key_to_name:
                    key_to_name[key] = name

    interactions = interaction_staging.copy()
    interactions["source_drug_id"] = interactions["source_label_id"].astype(str)
    interactions = interactions[
        [
            "source_drug_id",
            "source_label_id",
            "section_name",
            "text_snippet",
            "mention_key",
            "mention_text",
        ]
    ]

    # Resolve only unambiguous keys (one key maps to exactly one drug_id).
    unambiguous_target: dict[str, str] = {
        key: next(iter(ids)) for key, ids in key_to_ids.items() if len(ids) == 1
    }
    interactions["target_drug_id"] = interactions["mention_key"].map(unambiguous_target)
    interactions["matched_name"] = interactions["mention_key"].map(key_to_name)

    resolved = interactions[interactions["target_drug_id"].notna()].copy()
    resolved = resolved[resolved["source_drug_id"] != resolved["target_drug_id"]]
    resolved["relationship_type"] = "INTERACTS_WITH"
    resolved["confidence_score"] = CONFIDENCE_BY_REL["INTERACTS_WITH"]
    resolved = resolved.drop_duplicates(
        subset=["source_drug_id", "target_drug_id", "section_name", "mention_key"]
    )

    unresolved = interactions[interactions["target_drug_id"].isna()].copy()
    unresolved = unresolved.drop_duplicates(
        subset=["source_drug_id", "section_name", "mention_key", "mention_text"]
    )

    resolved_cols = [
        "source_drug_id",
        "target_drug_id",
        "relationship_type",
        "source_label_id",
        "section_name",
        "text_snippet",
        "mention_key",
        "matched_name",
        "confidence_score",
    ]
    unresolved_cols = [
        "source_drug_id",
        "source_label_id",
        "section_name",
        "mention_key",
        "mention_text",
        "text_snippet",
    ]

    return resolved[resolved_cols].reset_index(drop=True), unresolved[unresolved_cols].reset_index(
        drop=True
    )
