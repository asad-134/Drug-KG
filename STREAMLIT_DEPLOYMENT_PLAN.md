# Streamlit App Plan and Deployment (Streamlit Cloud)

## Codebase Structure (Current)

```
PHASE1_README.md
PHASE2_README.md
PHASE3_README.md
proposal.md
requirements.txt
STREAMLIT_DEPLOYMENT_PLAN.md

drug-labels/
  drug-label-0001-of-0013.json

outputs/
  phase1/
    profiling/
    staging/

prompts/
  safety_system_prompt.txt

scripts/
  demo_query.py
  run_phase1.py
  run_phase2.py
  snapshot_schema.py

src/
  phase1/
    __init__.py
    config.py
    extractors.py
    io_utils.py
    pipeline.py
    text_utils.py
  phase2/
    __init__.py
    config.py
    pipeline.py
    validate.py
  phase3/
    __init__.py
    config.py
    llm_chain.py
    prompting.py
    safety.py
    schema_snapshot.py
```

## Step-by-Step Plan

### Step 1: Define Streamlit App Scope

- Decide the first version features:
  - Single input box for a user question.
  - Button to run query.
  - Text response area with safety disclaimer appended.
  - Optional section to show generated Cypher.
- Choose the app entry file path (recommended):
  - `streamlit_app.py` at repo root.

### Step 2: Create a Minimal Streamlit UI

- Add `streamlit_app.py` with:
  - Title and disclaimer notice.
  - Text input for question.
  - Submit button.
  - Call your Phase 3 chain to run queries.
- Use `phase3.llm_chain.build_graph_chain` and `phase3.safety.validate_response`.
- Read `.env` for local runs, but use Streamlit secrets in cloud.

### Step 3: Add Runtime Configuration

- Ensure `requirements.txt` has all runtime dependencies:
  - `streamlit`
  - `langchain-neo4j`
  - `langchain-openai`
  - `neo4j`
  - `python-dotenv`
- Confirm `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, `OPENROUTER_API_KEY` are configurable.

### Step 4: Local Test

- Run locally:
  - `streamlit run streamlit_app.py`
- Validate:
  - Graph connection works.
  - LLM response returns.
  - Safety filter appends disclaimer.

### Step 5: Prep for Streamlit Cloud

- Push repo to GitHub (public or private).
- In Streamlit Cloud, create a new app:
  - Repo: your GitHub repo
  - Branch: main
  - Main file path: `streamlit_app.py`

### Step 6: Configure Secrets in Streamlit Cloud

- Add secrets in Streamlit Cloud (Settings -> Secrets):
  - `NEO4J_URI`
  - `NEO4J_USER`
  - `NEO4J_PASSWORD`
  - `OPENROUTER_API_KEY`
- Optional:
  - `OPENROUTER_MODEL`
  - `OPENROUTER_BASE_URL`
  - `SAFETY_DISCLAIMER`

### Step 7: Deploy and Verify

- Deploy the app from Streamlit Cloud.
- Run a few demo queries and verify:
  - Response quality.
  - Cypher generation is valid.
  - Safety disclaimer always appears.

### Step 8: Post-Deploy Hardening

- Add caching for the graph chain initialization.
- Add request timeouts and error handling.
- Add a small "About" section explaining educational use.
- Add a Cypher preview toggle (if desired).

## Optional Enhancements

- Add a history sidebar of recent questions.
- Add a status badge for Neo4j connectivity.
- Add a tab to show schema snapshot summary.
