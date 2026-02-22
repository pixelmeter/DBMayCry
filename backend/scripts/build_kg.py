"""
Populates Neo4j from an already-extracted schema.
Run AFTER app.py has generated the artifacts.

Usage
─────
    # fastest — uses existing artifacts
    python3 scripts/build_kg.py --schema-json artifacts/bike_store/bike_store_schema.json

    # reconnect to DB directly
    python3 scripts/build_kg.py --db-path bike_store.db
"""

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from connectors.sqlite import SQLiteConnector
from exporters.kg_builder import KnowledgeGraphBuilder


def load_from_json(schema_path: str) -> dict:
    schema_path = Path(schema_path)
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema JSON not found: {schema_path}")
    with open(schema_path) as f:
        return json.load(f)


def load_from_db(db_path: str) -> dict:
    """Re-connect to SQLite and extract schema."""
    connector = SQLiteConnector(filepath=db_path)
    connector.connect()
    schema = connector.extract_schema()
    connector.close()
    return schema


def main():
    parser = argparse.ArgumentParser(description="Populate Neo4j KG from DB schema.")
    parser.add_argument(
        "--schema-json",
        help="Path to existing *_schema.json artifact (fastest).",
        default=None,
    )
    parser.add_argument(
        "--db-path",
        help="Path to SQLite .db file if no --schema-json given.",
        default=os.getenv("SQLITE_FILE", "bike_store.db"),
    )
    args = parser.parse_args()

    # Load schema
    if args.schema_json:
        print(f"[KG] Loading from JSON: {args.schema_json}")
        schema = load_from_json(args.schema_json)
    else:
        print(f"[KG] Connecting to: {args.db_path}")
        schema = load_from_db(args.db_path)

    db_name = schema.get("database", "unknown")
    print(f"[KG] Database: {db_name}  |  Tables: {len(schema['tables'])}")

    # Build graph
    neo4j_uri  = os.getenv("NEO4J_URI")
    neo4j_user = os.getenv("NEO4J_USER")
    neo4j_pass = os.getenv("NEO4J_PASSWORD")

    if not all([neo4j_uri, neo4j_user, neo4j_pass]):
        raise EnvironmentError(
            "Missing Neo4j credentials. Set NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD in .env"
        )

    with KnowledgeGraphBuilder(neo4j_uri, neo4j_user, neo4j_pass) as kg:
        kg.build(schema)

    print("\nKnowledge graph populated successfully.")


if __name__ == "__main__":
    main()