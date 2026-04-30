from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from .config import Phase1Config
from .extractors import (
    build_drug_row,
    extract_mentions,
    section_text,
)
from .io_utils import iter_records, shard_paths
from .text_utils import stable_id


@dataclass(slots=True)
class Phase1Result:
    total_records: int
    output_dir: Path


def run_phase1(config: Phase1Config) -> Phase1Result:
    config.ensure_dirs()

    shards = shard_paths(config.input_dir)
    if not shards:
        raise FileNotFoundError(f"No shard files found in {config.input_dir}")

    total_records = 0
    section_presence = Counter()
    section_nonempty_items = Counter()

    drugs_rows: list[dict[str, Any]] = []
    indication_rows: list[dict[str, str]] = []
    adverse_rows: list[dict[str, str]] = []
    contraindication_rows: list[dict[str, str]] = []
    interaction_rows: list[dict[str, str]] = []

    # First pass: profile + staging rows except interaction target linking.
    for record in iter_records(config.input_dir):
        total_records += 1

        for section in config.target_sections:
            text_items = section_text(record, section)
            if text_items:
                section_presence[section] += 1
                section_nonempty_items[section] += len(text_items)

        drug_row = build_drug_row(record)
        drugs_rows.append(drug_row)

        source_id = drug_row["source_id"]

        indication_rows.extend(
            extract_mentions(
                source_id=source_id,
                section="indications_and_usage",
                section_text_items=section_text(record, "indications_and_usage"),
                mention_type="condition",
            )
        )
        adverse_rows.extend(
            extract_mentions(
                source_id=source_id,
                section="adverse_reactions",
                section_text_items=section_text(record, "adverse_reactions"),
                mention_type="side_effect",
            )
        )
        contraindication_rows.extend(
            extract_mentions(
                source_id=source_id,
                section="contraindications",
                section_text_items=section_text(record, "contraindications"),
                mention_type="condition",
            )
        )

        interaction_rows.extend(
            extract_mentions(
                source_id=source_id,
                section="drug_interactions",
                section_text_items=section_text(record, "drug_interactions"),
                mention_type="interaction",
            )
        )

    drugs_df = pd.DataFrame(drugs_rows).drop_duplicates(subset=["source_id"])

    indications_df = pd.DataFrame(indication_rows)
    adverse_df = pd.DataFrame(adverse_rows)
    contraindications_df = pd.DataFrame(contraindication_rows)
    interactions_df = pd.DataFrame(interaction_rows)

    # Add normalized IDs for graph staging.
    if not indications_df.empty:
        indications_df["condition_id"] = indications_df["mention_key"].map(
            lambda x: stable_id("condition", str(x))
        )
    if not contraindications_df.empty:
        contraindications_df["condition_id"] = contraindications_df["mention_key"].map(
            lambda x: stable_id("condition", str(x))
        )
    if not adverse_df.empty:
        adverse_df["effect_id"] = adverse_df["mention_key"].map(
            lambda x: stable_id("effect", str(x))
        )

    _write_profile_outputs(
        config=config,
        total_records=total_records,
        section_presence=section_presence,
        section_nonempty_items=section_nonempty_items,
        shards=shards,
    )

    _write_mapping_doc(config)

    _write_staging_csv(config.staging_dir / "drugs_staging.csv", drugs_df)
    _write_staging_csv(
        config.staging_dir / "indication_mentions_staging.csv", indications_df
    )
    _write_staging_csv(
        config.staging_dir / "adverse_effect_mentions_staging.csv", adverse_df
    )
    _write_staging_csv(
        config.staging_dir / "interaction_mentions_staging.csv", interactions_df
    )
    _write_staging_csv(
        config.staging_dir / "contraindication_mentions_staging.csv", contraindications_df
    )

    return Phase1Result(total_records=total_records, output_dir=config.output_dir)


def _write_staging_csv(path: Path, df: pd.DataFrame) -> None:
    if df.empty:
        pd.DataFrame().to_csv(path, index=False)
        return
    df.to_csv(path, index=False)


def _write_profile_outputs(
    *,
    config: Phase1Config,
    total_records: int,
    section_presence: Counter,
    section_nonempty_items: Counter,
    shards: list[Path],
) -> None:
    rows: list[dict[str, Any]] = []
    for section in config.target_sections:
        present = section_presence.get(section, 0)
        rows.append(
            {
                "section": section,
                "records_with_section": present,
                "coverage_percent": round((present / total_records) * 100, 4)
                if total_records
                else 0.0,
                "nonempty_item_count": section_nonempty_items.get(section, 0),
            }
        )

    coverage_df = pd.DataFrame(rows)
    coverage_df.to_csv(config.profiling_dir / "openfda_field_coverage.csv", index=False)

    summary = {
        "total_shards": len(shards),
        "total_records": total_records,
        "target_sections": list(config.target_sections),
        "coverage_report": "profiling/openfda_field_coverage.csv",
    }
    (config.profiling_dir / "profile_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )


def _write_mapping_doc(config: Phase1Config) -> None:
    lines = [
        "# OpenFDA Field Mapping (Phase 1)",
        "",
        "This mapping is generated for the OpenFDA-only Phase 1 pipeline.",
        "",
        "## Entity Sources",
        "",
        "- Drug",
        "  - source_id: set_id or id",
        "  - generic_name: openfda.generic_name[0]",
        "  - brand_names: openfda.brand_name[*]",
        "  - substance_names: openfda.substance_name[*]",
        "  - manufacturer_name: openfda.manufacturer_name[0]",
        "  - route: openfda.route[0]",
        "",
        "- Condition mentions",
        "  - indications_and_usage -> TREATS candidates",
        "  - contraindications -> CONTRAINDICATED_IN candidates",
        "",
        "- Side effect mentions",
        "  - adverse_reactions -> HAS_SIDE_EFFECT candidates",
        "",
        "- Interaction mentions",
        "  - drug_interactions -> INTERACTS_WITH candidates",
        "",
        "## Evidence Properties",
        "",
        "All mention rows include:",
        "- source_label_id",
        "- section_name",
        "- mention_text",
        "- mention_key (normalized)",
        "- text_snippet",
    ]
    config.mapping_doc_path.write_text("\n".join(lines), encoding="utf-8")
