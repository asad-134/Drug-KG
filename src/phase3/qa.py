from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from langchain_neo4j import GraphCypherQAChain
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from .llm_chain import (
    build_cypher_prompt,
    build_graph,
    build_llm,
    load_graph_qa_config,
)
from .safety import validate_response


VERIFICATION_REJECTED = "VERIFICATION_REJECTED"
REJECTION_RESPONSE = (
    "I could not verify that response against the graph results, so I cannot provide a factual answer."
)


_WORD_RE = re.compile(r"[a-zA-Z0-9]+")


@dataclass(slots=True)
class ResolutionResult:
    original_question: str
    resolved_question: str
    matched_phrase: str | None
    matched_name: str | None
    score: float | None

    @property
    def used(self) -> bool:
        return bool(self.matched_name and self.matched_phrase)


@dataclass(slots=True)
class QAResources:
    chain: GraphCypherQAChain
    verifier_llm: ChatOpenAI
    drug_names: list[str]


def _normalize(text: str) -> str:
    lowered = text.lower()
    lowered = re.sub(r"[^a-z0-9\s]", " ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


def _candidate_phrases(question: str) -> list[str]:
    tokens = _WORD_RE.findall(question.lower())
    phrases: list[str] = []
    for size in (1, 2, 3):
        for idx in range(len(tokens) - size + 1):
            phrase = " ".join(tokens[idx : idx + size]).strip()
            if len(phrase) >= 3:
                phrases.append(phrase)
    return phrases


def _best_fuzzy_match(phrases: list[str], drug_names: list[str], cutoff: float) -> tuple[str | None, str | None, float | None]:
    best_phrase = None
    best_name = None
    best_score = None

    for phrase in phrases:
        for name in drug_names:
            score = SequenceMatcher(None, phrase, name).ratio()
            if score < cutoff:
                continue
            if best_score is None or score > best_score:
                best_score = score
                best_phrase = phrase
                best_name = name

    return best_phrase, best_name, best_score


def resolve_question(question: str, drug_names: list[str]) -> ResolutionResult:
    normalized_question = _normalize(question)
    for name in drug_names:
        if name and name in normalized_question:
            return ResolutionResult(
                original_question=question,
                resolved_question=question,
                matched_phrase=None,
                matched_name=None,
                score=None,
            )

    cutoff = float(os.getenv("DRUG_MATCH_CUTOFF", "0.86"))
    phrases = _candidate_phrases(question)
    matched_phrase, matched_name, score = _best_fuzzy_match(phrases, drug_names, cutoff)
    if not matched_name or not matched_phrase:
        return ResolutionResult(
            original_question=question,
            resolved_question=question,
            matched_phrase=None,
            matched_name=None,
            score=None,
        )

    resolved_question = re.sub(
        re.escape(matched_phrase),
        matched_name,
        question,
        count=1,
        flags=re.IGNORECASE,
    )
    return ResolutionResult(
        original_question=question,
        resolved_question=resolved_question,
        matched_phrase=matched_phrase,
        matched_name=matched_name,
        score=score,
    )


def _extract_context(response: dict[str, Any]) -> list[dict[str, Any]]:
    intermediate = response.get("intermediate_steps", [])
    if isinstance(intermediate, list):
        for step in intermediate:
            if isinstance(step, dict) and "context" in step:
                context = step.get("context")
                if isinstance(context, list):
                    return context
            if isinstance(step, (list, tuple)) and len(step) >= 2:
                context_candidate = step[-1]
                if isinstance(context_candidate, list):
                    return context_candidate
    context = response.get("context")
    return context if isinstance(context, list) else []


def build_qa_resources(project_root: Path) -> QAResources:
    cfg = load_graph_qa_config(project_root)
    graph = build_graph(project_root)
    cypher_prompt = build_cypher_prompt()
    chain = GraphCypherQAChain.from_llm(
        build_llm(cfg),
        graph=graph,
        cypher_prompt=cypher_prompt,
        verbose=True,
        allow_dangerous_requests=True,
        return_intermediate_steps=True,
    )

    verifier_model = os.getenv("OPENROUTER_VERIFY_MODEL", cfg.openrouter_model)
    verifier_llm = build_llm(cfg, model_override=verifier_model, max_tokens=500)

    drug_names = [
        row["name"]
        for row in graph.query(
            "MATCH (d:Drug) WHERE d.normalized_name IS NOT NULL RETURN d.normalized_name AS name"
        )
        if isinstance(row.get("name"), str) and row["name"].strip()
    ]

    return QAResources(chain=chain, verifier_llm=verifier_llm, drug_names=drug_names)


def verify_answer(verifier_llm: ChatOpenAI, *, question: str, answer: str, context: list[dict[str, Any]]) -> str:
    context_json = json.dumps(context, ensure_ascii=True, default=str)
    system_text = (
        "You are a strict medical QA fact checker.\n"
        "Only use the provided graph results to verify claims.\n"
        "If the answer contains claims not supported by the results, remove them.\n"
        "If nothing is supported, respond with exactly: VERIFICATION_REJECTED\n"
        "Return only the corrected answer or VERIFICATION_REJECTED, no extra commentary."
    )
    user_text = (
        f"Question: {question}\n\n"
        f"Graph results (JSON): {context_json}\n\n"
        f"Draft answer: {answer}"
    )
    messages = [SystemMessage(content=system_text), HumanMessage(content=user_text)]
    verified = verifier_llm.invoke(messages)
    return verified.content.strip()


def run_verified_query(question: str, resources: QAResources) -> tuple[str, ResolutionResult]:
    resolution = resolve_question(question, resources.drug_names)
    response = resources.chain.invoke({"query": resolution.resolved_question})
    text = response.get("result", "") if isinstance(response, dict) else str(response)

    context = _extract_context(response) if isinstance(response, dict) else []
    verified = verify_answer(resources.verifier_llm, question=question, answer=text, context=context)
    if verified.strip() == VERIFICATION_REJECTED:
        safety = validate_response(REJECTION_RESPONSE)
        return safety.sanitized_text, resolution

    safety = validate_response(verified)
    return safety.sanitized_text, resolution
