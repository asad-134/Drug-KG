import os
import pandas as pd
from neo4j import GraphDatabase
from dotenv import load_dotenv
from pathlib import Path

# Setup paths and Config
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "outputs" / "phase2" / "graph"
load_dotenv(PROJECT_ROOT / ".env", override=True)

URI = os.getenv("NEO4J_URI", "")
USER = os.getenv("NEO4J_USER", "")
PASSWORD = os.getenv("NEO4J_PASSWORD", "")

def run_import():
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    
    with driver.session() as session:
        # --- PHASE 1: CLEANUP & SCHEMA ---
        print("Cleaning existing schema and setting up Constraints...")
        
        # 1. Drop potentially conflicting indexes first
        # We try to drop them by common names or patterns
        try:
            session.run("DROP INDEX condition_id_idx IF EXISTS")
            session.run("DROP INDEX drug_id_idx IF EXISTS")
        except Exception as e:
            print(f"Index cleanup skipped or not needed: {e}")

        # 2. Create Unique Constraints
        # These automatically create high-performance UNIQUE indexes
        session.run("CREATE CONSTRAINT drug_id_unique IF NOT EXISTS FOR (d:Drug) REQUIRE d.drug_id IS UNIQUE")
        session.run("CREATE CONSTRAINT condition_id_unique IF NOT EXISTS FOR (c:Condition) REQUIRE c.condition_id IS UNIQUE")
        
        # 3. Create a plain index for Side Effects (since they might not be unique in all datasets)
        session.run("CREATE INDEX effect_id_idx IF NOT EXISTS FOR (s:SideEffect) ON (s.effect_id)")

        # --- PHASE 2: BATCH DATA INGESTION ---
        print("Pushing Drug nodes...")
        drugs_df = pd.read_csv(DATA_DIR / "drugs.csv").fillna("")
        session.run("""
            UNWIND $rows AS row
            MERGE (d:Drug {drug_id: row.drug_id})
            SET d += row
        """, rows=drugs_df.to_dict('records'))
        # 2. Import Conditions
        print("Pushing Condition nodes...")
        conditions_df = pd.read_csv(DATA_DIR / "conditions.csv").fillna("")
        session.run("""
            UNWIND $rows AS row
            MERGE (c:Condition {condition_id: row.condition_id})
            SET c += row
        """, rows=conditions_df.to_dict('records'))

        # 3. Import Side Effects (Creating nodes from the target IDs)
        print("Pushing SideEffect nodes...")
        se_df = pd.read_csv(DATA_DIR / "has_side_effect.csv")[['target_effect_id']].drop_duplicates()
        session.run("""
            UNWIND $rows AS row
            MERGE (s:SideEffect {effect_id: row.target_effect_id})
        """, rows=se_df.to_dict('records'))

        # 4. Import Relationships: TREATS
        print("Creating TREATS relationships...")
        treats_df = pd.read_csv(DATA_DIR / "treats.csv").fillna("")
        session.run("""
            UNWIND $rows AS row
            MATCH (d:Drug {drug_id: row.source_drug_id})
            MATCH (c:Condition {condition_id: row.target_condition_id})
            MERGE (d)-[r:TREATS]->(c)
            SET r += row
        """, rows=treats_df.to_dict('records'))

        # 5. Import Relationships: HAS_SIDE_EFFECT
        print("Creating HAS_SIDE_EFFECT relationships...")
        has_se_df = pd.read_csv(DATA_DIR / "has_side_effect.csv").fillna("")
        session.run("""
            UNWIND $rows AS row
            MATCH (d:Drug {drug_id: row.source_drug_id})
            MATCH (s:SideEffect {effect_id: row.target_effect_id})
            MERGE (d)-[r:HAS_SIDE_EFFECT]->(s)
            SET r += row
        """, rows=has_se_df.to_dict('records'))

        # 6. Import Relationships: INTERACTS_WITH
        print("Creating INTERACTS_WITH relationships...")
        interacts_df = pd.read_csv(DATA_DIR / "interacts_with.csv").fillna("")
        session.run("""
            UNWIND $rows AS row
            MATCH (d1:Drug {drug_id: row.source_drug_id})
            MATCH (d2:Drug {drug_id: row.target_drug_id})
            MERGE (d1)-[r:INTERACTS_WITH]->(d2)
            SET r += row
        """, rows=interacts_df.to_dict('records'))
        # 7. Import Relationships: CONTRAINDICATED_IN
        print("Creating CONTRAINDICATED_IN relationships...")
        contra_df = pd.read_csv(DATA_DIR / "contraindicated_in.csv").fillna("")
        session.run("""
            UNWIND $rows AS row
            MATCH (d:Drug {drug_id: row.source_drug_id})
            MATCH (c:Condition {condition_id: row.target_condition_id})
            MERGE (d)-[r:CONTRAINDICATED_IN]->(c)
            SET r += row
        """, rows=contra_df.to_dict('records'))

    driver.close()
    print("\n--- Cloud Database Populated Successfully! ---")

if __name__ == "__main__":
    run_import()
