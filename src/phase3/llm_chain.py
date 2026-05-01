from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
from langchain_openai import ChatOpenAI
# Import the PromptTemplate class
from langchain_core.prompts import PromptTemplate

@dataclass(slots=True)
class GraphQAConfig:
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    openrouter_api_key: str
    openrouter_base_url: str
    openrouter_model: str


def load_graph_qa_config(project_root: Path) -> GraphQAConfig:
    return GraphQAConfig(
        # FIX: Changed port from 7474 to 7687 for the Bolt protocol
        neo4j_uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        neo4j_user=os.getenv("NEO4J_USER", "neo4j"),
        neo4j_password=os.getenv("NEO4J_PASSWORD", "neo4j_134"),
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY", ""),
        openrouter_base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        openrouter_model=os.getenv("OPENROUTER_MODEL", "google/gemma-4-31b-it:free"),
    )


def build_graph_chain(project_root: Path) -> GraphCypherQAChain:
    cfg = load_graph_qa_config(project_root)

    graph = Neo4jGraph(
        url=cfg.neo4j_uri,
        username=cfg.neo4j_user,
        password=cfg.neo4j_password,
    )

    cypher_prompt_text = (
        "You are an expert Neo4j Cypher generator.\n"
        "Given the graph schema and a user question, write a Cypher query that answers the question.\n"
        "Use only the labels, relationship types, and properties present in the schema.\n"
        "When matching names, prefer the normalized_name property and make comparisons case-insensitive,\n"
        "for example: toLower(d.normalized_name) = toLower('gabapentin').\n"
        "For yes/no questions, do NOT use EXISTS() without a pattern. Use a count-based boolean,\n"
        "for example: MATCH (a:Drug)-[:INTERACTS_WITH]->(b:Drug)\n"
        "RETURN count(*) > 0 AS has_interaction.\n"
        "Return only the Cypher query, with no explanations or formatting.\n\n"
        "Schema:\n{schema}\n\n"
        "Question:\n{question}\n"
    )
    CYPHER_GENERATION_PROMPT = PromptTemplate(
        input_variables=["schema", "question"],
        template=cypher_prompt_text,
    )

    llm = ChatOpenAI(
        api_key=cfg.openrouter_api_key,
        base_url=cfg.openrouter_base_url,
        model=cfg.openrouter_model,
        temperature=0.0,
        max_tokens=800,
        default_headers={"HTTP-Referer": "local", "X-Title": "OpenFDA-DDKG"},
    )

    return GraphCypherQAChain.from_llm(
        llm,
        graph=graph,
        cypher_prompt=CYPHER_GENERATION_PROMPT,
        verbose=True,
        allow_dangerous_requests=True # Required in newer LangChain versions
    )