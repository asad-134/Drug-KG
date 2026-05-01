import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
from pathlib import Path

# Load config
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env", override=True)

URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
USER = os.getenv("NEO4J_USER", "")
PASSWORD = os.getenv("NEO4J_PASSWORD", "")

# Define the ingestion queries
LITE_IMPORT_QUERIES = [
    # 1. Create Constraints
    "CREATE CONSTRAINT drug_id IF NOT EXISTS FOR (d:Drug) REQUIRE d.drug_id IS UNIQUE",
    #2 . Create indexes
    "CREATE INDEX drug_id_idx FOR (d:Drug) ON (d.drug_id)",
    "CREATE INDEX condition_id_idx FOR (c:Condition) ON (c.condition_id)",
    "CREATE INDEX effect_id_idx FOR (s:SideEffect) ON (s.effect_id)",
    # 2. Import Drugs (Limit to 500 for Lite version)
    """
    LOAD CSV WITH HEADERS FROM 'file:///drugs.csv' AS row
    WITH row SKIP 0 LIMIT 100000
    MERGE (d:Drug {drug_id: row.drug_id})
    SET d += row
    """,
    
    # 3. Import Diseases
    """
    LOAD CSV WITH HEADERS FROM 'file:///conditions.csv' AS row
    WITH row SKIP 0 LIMIT 100000
    MERGE (c:Condition {condition_id: row.condition_id})
    SET c += row
    """,

    """
    LOAD CSV WITH HEADERS FROM 'file:///treats.csv' AS row
    WITH row SKIP 0 LIMIT 100000
    MATCH (d:Drug {drug_id: row.source_drug_id})
    MATCH (c:Condition {condition_id: row.target_condition_id})
    MERGE (d)-[r:TREATS]->(c)
    SET r += row
    """,
    # 4. Import Relationships (TREATS)
    """
    LOAD CSV WITH HEADERS FROM 'file:///treats.csv' AS row
    WITH row SKIP 0 LIMIT 100000
    MATCH (d:Drug {drug_id: row.source_drug_id})
    MATCH (c:Condition {condition_id: row.target_condition_id})
    MERGE (d)-[r:TREATS]->(c)
    SET r += row
    """,

    """
    LOAD CSV WITH HEADERS FROM 'file:///has_side_effect.csv' AS row
    WITH row SKIP 0 LIMIT 100000
    MATCH (d:Drug {drug_id: row.source_drug_id})
    MATCH (s:SideEffect {effect_id: row.target_effect_id})
    MERGE (d)-[r:HAS_SIDE_EFFECT]->(s)
    SET r += row
    """,
    """
    LOAD CSV WITH HEADERS FROM 'file:///interacts_with.csv' AS row
    WITH row SKIP 0 LIMIT 100000
    MATCH (d1:Drug {drug_id: row.source_drug_id})
    MATCH (d2:Drug {drug_id: row.target_drug_id})
    MERGE (d1)-[r:INTERACTS_WITH]->(d2)
    SET r += row
    """,

]

def run_import():
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    with driver.session() as session:
        for query in LITE_IMPORT_QUERIES:
            print(f"Executing: {query[:50]}...")
            session.run(query)
    driver.close()
    print("Lite Database Populated Successfully!")

if __name__ == "__main__":
    run_import()