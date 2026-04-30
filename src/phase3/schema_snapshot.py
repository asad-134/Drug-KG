from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from neo4j import GraphDatabase


@dataclass(slots=True)
class Neo4jConfig:
    uri: str
    user: str
    password: str


def load_neo4j_config() -> Neo4jConfig:
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "changeme")
    return Neo4jConfig(uri=uri, user=user, password=password)


def _run_query(driver, query: str) -> list[dict[str, object]]:
    with driver.session() as session:
        result = session.run(query)
        return [record.data() for record in result]


def snapshot_schema(output_path: Path) -> Path:
    cfg = load_neo4j_config()
    driver = GraphDatabase.driver(cfg.uri, auth=(cfg.user, cfg.password))
    try:
        labels = _run_query(driver, "CALL db.labels()")
        rels = _run_query(driver, "CALL db.relationshipTypes()")
        props = _run_query(
            driver,
            "CALL db.schema.nodeTypeProperties() YIELD nodeType, propertyName, propertyTypes "
            "RETURN nodeType, propertyName, propertyTypes",
        )
    finally:
        driver.close()

    snapshot = {
        "labels": sorted([row["label"] for row in labels]),
        "relationship_types": sorted([row["relationshipType"] for row in rels]),
        "node_properties": props,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    return output_path
