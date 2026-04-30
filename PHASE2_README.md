# Phase 2 Graph Build and Validation

This phase converts Phase 1 staging outputs into graph-ready node and relationship CSVs,
then runs a validation pass with structural, orphan, provenance, and semantic checks.

## Run

python scripts/run_phase2.py

## Outputs

Generated under outputs/phase2:

- phase2_stats.json
- graph/drugs.csv
- graph/conditions.csv
- graph/side_effects.csv
- graph/treats.csv
- graph/has_side_effect.csv
- graph/contraindicated_in.csv
- graph/interacts_with.csv
- validation/interaction_unresolved.csv
- validation/suspicious_terms.csv
- validation/validation_report.json

## Benchmarks

Use neo4j/phase2_benchmark_queries.cypher for baseline query validation.

## Before Phase 3

Run these checks before moving to Phase 3:

1. Re-run Phase 2 with latest filters:
	python scripts/run_phase2.py
2. Inspect validation summary:
	outputs/phase2/validation/validation_report.json
3. Confirm suspicious terms are near zero and review:
	outputs/phase2/validation/suspicious_terms.csv
4. Review unresolved interaction mentions and sample rows:
	outputs/phase2/validation/interaction_unresolved.csv
5. Verify graph row counts and stats:
	outputs/phase2/phase2_stats.json
6. Import graph CSVs into Neo4j and run benchmark queries:
	neo4j/phase2_benchmark_queries.cypher
