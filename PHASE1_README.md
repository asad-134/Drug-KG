# Phase 1 OpenFDA Pipeline

This repository now includes a runnable Phase 1 implementation for:

1. OpenFDA shard profiling and section coverage reporting
2. Drug metadata staging extraction
3. Condition, side effect, contraindication, and interaction mention staging extraction
4. Field mapping document generation

## Run

From the project root:

python scripts/run_phase1.py

## Outputs

Generated under outputs/phase1:

- openfda_field_mapping.md
- profiling/profile_summary.json
- profiling/openfda_field_coverage.csv
- staging/drugs_staging.csv
- staging/indication_mentions_staging.csv
- staging/adverse_effect_mentions_staging.csv
- staging/interaction_mentions_staging.csv
- staging/contraindication_mentions_staging.csv

## Notes

- The interaction extraction is lexicon-based in Phase 1 and intentionally conservative.
- Mention extraction is rule-based to support transparent review before Phase 2 graph import.
