# Phase 3: LLM QA + Safety Setup (Steps 1-3)

This phase adds Neo4j schema snapshotting, GraphCypherQAChain integration, and safety validation.

## Step 1: Neo4j Connection + Schema Snapshot

1. Copy .env.example to .env and fill in your Neo4j credentials.
2. Run schema snapshot:

python scripts/snapshot_schema.py

Output:
- outputs/phase3/neo4j_schema_snapshot.json

## Step 2: GraphCypherQAChain Integration

- Module: src/phase3/llm_chain.py
- Uses OpenRouter via langchain_openai (OpenAI-compatible API)
- Requires OPENROUTER_API_KEY in .env

## Step 3: Safety Prompt and Output Validation

- System prompt: prompts/safety_system_prompt.txt
- Validation utility: src/phase3/safety.py

## Notes

- Keep prompts and logs local.
- Do not provide medical advice or dosage guidance.
- Always append the safety disclaimer to responses.
