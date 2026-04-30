# PROJECT PROPOSAL



*Intelligent, Safety-First Medical Information Retrieval Using Knowledge Graphs & LLMs*



## 1. Executive Summary

This proposal describes the design and implementation of a Drug-Disease Knowledge Graph (DDKG) — an open-source, locally deployable educational tool that organises structured pharmacological data into an interactive, queryable graph. Users — students, researchers, and healthcare educators — can ask natural-language questions such as "What drugs treat hypertension?", "What are the side effects of ibuprofen?", or "Which medications interact with warfarin?" and receive accurate, citation-linked answers.

> **⚠ EDUCATIONAL USE DISCLAIMER:** This system is designed strictly for educational and research purposes. It must not be used as a substitute for professional medical advice, diagnosis, or treatment.

The stack is built entirely on free, open-licensed resources: DrugBank's open subset or OpenFDA drug labels for data; Neo4j Community for graph storage; pandas for ingestion; LangChain's GraphCypherQAChain for retrieval; and a locally run Mistral 7B LLM for answer generation — with mandatory safety guardrails applied at every inference step.

---

## 2. Problem Statement & Motivation

### 2.1 The Medical Information Gap

Pharmacological knowledge is sprawling, deeply interconnected, and critically important — yet existing tools either hide it behind paywalls (clinical databases), bury it in unstructured text (package inserts), or fail to expose relational structure (flat CSV exports). Medical and pharmacy students, AI/NLP researchers, and public health educators all need a lightweight, structured, queryable drug knowledge base they can run locally.

| **Core Educational Needs This Project Addresses** |
|----------------------------------------------------|
| - Students need to query drug–disease mappings without navigating dense clinical references |
| - Researchers need structured, machine-readable pharmacological relationships for downstream NLP tasks |
| - Educators need a safe, sandboxed tool to demonstrate knowledge graph and LLM integration |
| - Public health analysts need interaction and contraindication data in a programmatic format |

### 2.2 Why a Knowledge Graph?

Flat datasets cannot express multi-hop relationships like "drugs that treat condition X but interact with drug Y, which is metabolised by enzyme Z." A property graph natively models these chains, enabling traversal queries that are impossible with tabular joins at scale. Combined with a local LLM, the system translates natural language into Cypher queries, executes them against Neo4j, and returns coherent, grounded answers.

---

## 3. System Architecture

### 3.1 Architectural Overview

The DDKG system is organised across five functional layers, each independently replaceable:

| **Layer** | **Responsibility** |
|-----------|-------------------|
| Data Acquisition | Download DrugBank open dataset (XML) or OpenFDA drug label JSON; optionally supplement with the Kaggle 'Drugs' dataset for side-effect coverage |
| Data Processing | pandas pipelines parse, normalise, and deduplicate drug names, indications, side effects, and interactions; output to CSV for Neo4j bulk import |
| Graph Storage | Neo4j Community stores the property graph; Cypher constraints enforce data integrity; APOC library handles batch imports and graph algorithms |
| QA Retrieval | LangChain GraphCypherQAChain translates user questions to Cypher, executes queries, and retrieves structured results; a fallback vector search covers semantic queries |
| Answer Generation | Mistral 7B (via Ollama) generates fluent answers grounded in graph results, with a mandatory safety system prompt that disclaims clinical authority |

### 3.2 Knowledge Graph Schema

The graph encodes five node types and six directed relationship types:

| **Node / Relationship** | **Properties / Notes** |
|------------------------|------------------------|
| Drug | drug_id, name, generic_name, drug_class, half_life, bioavailability |
| Disease | disease_id, name, icd10_code, category (e.g., Cardiovascular) |
| SideEffect | effect_id, name, severity (mild / moderate / severe), frequency |
| Interaction | interaction_id, description, mechanism, severity_level |
| Enzyme | enzyme_id, name, gene_symbol — for metabolism relationships |
| TREATS | Drug → Disease; evidence_level, approval_status (FDA / off-label) |
| HAS_SIDE_EFFECT | Drug → SideEffect; incidence_rate, onset |
| INTERACTS_WITH | Drug → Drug via Interaction node; interaction_type |
| METABOLISED_BY | Drug → Enzyme; pathway (CYP3A4 etc.) |
| CONTRAINDICATED | Drug → Disease; reason, severity |
| BELONGS_TO_CLASS | Drug → DrugClass; classification hierarchy |

### 3.3 Query & Safety Pipeline

Every user query passes through a four-step pipeline before an answer is returned:

- **Step 1 — Intent Classification:** Classify query as structural (graph) or semantic (vector); route accordingly
- **Step 2 — Cypher Generation:** LangChain generates a validated Cypher query using few-shot prompting and a schema description; invalid queries are caught and retried
- **Step 3 — Graph Execution:** Neo4j executes the Cypher query and returns structured results (drug names, side effects, interaction warnings)
- **Step 4 — Safe Answer Generation:** Mistral 7B synthesises a natural-language answer with a non-negotiable system prompt prepended: results are labelled educational, users are directed to consult a healthcare professional

---

## 4. Technology Stack

| **Technology** | **Details** |
|----------------|-------------|
| Graph Database | Neo4j 5.x Community Edition — free, local, full Cypher support; APOC plugin for import/export |
| Data Processing | Python 3.11 + pandas — XML/JSON parsing, normalisation, deduplication; SQLite for intermediate staging |
| QA Orchestration | LangChain 0.2 — GraphCypherQAChain + ConversationalRetrievalChain for follow-up context |
| Vector Fallback | Chroma DB + sentence-transformers/all-MiniLM-L6-v2 for semantic similarity on drug descriptions |
| Language Model |any api of my choice through open router |
| Safety Layer | Custom LangChain output parser validates responses; strips any clinical directives; appends disclaimer |
| Backend API | FastAPI — /query, /graph, /explain endpoints; async Neo4j driver |
| Frontend | Streamlit — chat interface with expandable Cypher query viewer and graph subgraph visualisation |
| Data Sources | DrugBank Open (free academic), OpenFDA drug labels (public domain), Kaggle 'Drugs' side-effect dataset |

---

## 5. Implementation Plan

### 5.1 Development Phases

| **Phase** | **Timeline** | **Key Deliverables** |
|-----------|--------------|----------------------|
| Phase 1 | Weeks 1–2 | Data acquisition and licence verification; pandas parsing of DrugBank XML and OpenFDA JSON; schema design and Neo4j setup |
| Phase 2 | Weeks 3–4 | Bulk graph import (drugs, diseases, side effects, interactions); Cypher constraint setup; data quality validation queries |
| Phase 3 | Weeks 5–6 | LangChain GraphCypherQAChain integration;llm api; safety prompt engineering and output validation |
| Phase 4 | Weeks 7–8 | UI; Cypher query inspector; Chroma vector fallback; end-to-end QA accuracy testing |
| Phase 5 | Weeks 9–10 | Safety audit, edge-case hardening, documentation, Docker packaging, and demo dataset release, Deployment on web |

### 5.2 Sample Queries the System Will Support

| **Supported Query Types with Examples** |
|------------------------------------------|
| - Indication lookup: "What drugs are approved to treat Type 2 diabetes?" |
| - Side effect query: "What are the most severe side effects of metformin?" |
| - Interaction check: "Does ibuprofen interact with blood thinners?" (educational context, with disclaimer) |
| - Contraindication: "Which antihypertensives are contraindicated in pregnancy?" |
| - Drug class: "List all ACE inhibitors and their primary indications" |
| - Metabolism: "Which drugs are metabolised by the CYP3A4 enzyme?" |
| - Multi-hop: "Find drugs that treat hypertension but interact with warfarin" |

---

## 6. Safety, Ethics & Compliance

### 6.1 Mandatory Safety Guardrails

Because this system handles medical information, safety controls are non-optional and are implemented at multiple layers:

| **Control** | **Implementation** |
|-------------|-------------------|
| System Prompt Lock | Every inference request prepends a non-removable system prompt: the model must identify all outputs as educational and recommend professional consultation |
| Output Validation | A post-generation parser checks for prescriptive language ("you should take", "stop taking") and rewrites or rejects such outputs automatically |
| Severity Flagging | Any query returning HIGH-severity side effects or interactions triggers a bold on-screen disclaimer in the Streamlit UI |
| No Dosage Generation | Dosage recommendation queries are explicitly blocked at the intent classification layer; the system redirects users to authoritative sources |
| Source Attribution | Every answer cites its source node in the knowledge graph (DrugBank ID or OpenFDA application number) |

### 6.2 Data Licensing

- **DrugBank Open Data:** Creative Commons Attribution-NonCommercial 4.0 — free for academic, non-commercial use
- **OpenFDA Drug Labels:** Public domain (U.S. government work) — fully unrestricted
- **Kaggle Drugs Dataset:** CC0 Public Domain — fully unrestricted
- **All model weights (Mistral 7B):** Apache 2.0 licence — free for academic and commercial use

---

## 7. Risk Assessment

| **Risk** | **Severity** | **Mitigation** |
|----------|--------------|----------------|
| Medical misinformation from LLM | **High** | Multi-layer safety prompts; output parser blocks prescriptive language; mandatory disclaimers on all responses |
| Incomplete drug interaction data | **Medium** | Supplement DrugBank with OpenFDA; flag low-confidence answers; direct users to authoritative references |
| Neo4j memory limits on full dataset | **Low** | Start with a curated 5,000-drug subset; enable pagination; Neo4j AuraDB free tier as cloud fallback |
| Cypher query hallucinations | **Medium** | Schema-aware few-shot prompting; Cypher validator before execution; fallback to vector search on failure |
| DrugBank licence misuse | **Low** | Enforce non-commercial licence via README and application disclaimer; do not distribute raw DrugBank XML |
| User misinterprets output as clinical advice | **High** | Prominent UI disclaimers; all answers end with 'Consult a qualified healthcare provider'; no dosage data exposed |

---

## 8. Expected Outcomes & Success Metrics

| **Metric** | **Target** |
|------------|------------|
| QA Accuracy | ≥ 88% correct answers on a 100-question evaluation set covering indications, side effects, and interactions |
| Safety Compliance | 100% of responses include educational disclaimer; 0% contain dosage recommendations or clinical directives |
| Graph Coverage | ≥ 5,000 drugs, 2,000 diseases, 15,000 side-effect edges, 8,000 interaction edges at launch |
| Query Latency | End-to-end response under 10 seconds on 16 GB RAM hardware with Mistral 7B via Ollama |
| Cypher Success Rate | ≥ 90% of natural-language queries produce a valid, executable Cypher query on first attempt |
| User Comprehension | Pilot test with 10 pharmacy students: ≥ 80% rate answers as 'clear and educationally useful' |

---