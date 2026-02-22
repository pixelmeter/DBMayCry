# """
# Populates Neo4j from an already-extracted schema.
# Run this AFTER main.py has already generated the schema JSON artifacts.

# Usage
# ─────
#     uv run python scripts/build_kg.py                        # uses bike_store.db (default)
#     uv run python scripts/build_kg.py --db sqlite            # explicit
#     uv run python scripts/build_kg.py --db postgresql        # reads PG_* from .env
#     uv run python scripts/build_kg.py --schema-json artifacts/mydb_schema.json  # from file

# What it does
# ────────────
#   1. Loads schema — either from a saved JSON artifact OR by re-connecting to the DB
#   2. Optionally loads quality JSON if it exists alongside the schema JSON
#   3. Builds / updates the Neo4j knowledge graph (idempotent — safe to re-run)
# """

# import argparse
# import json
# import os
# import sys
# from pathlib import Path

# # ── make project root importable ─────────────────────────────────────────────
# ROOT = Path(__file__).resolve().parent.parent
# sys.path.insert(0, str(ROOT))
# os.chdir(ROOT)

# from dotenv import load_dotenv

# load_dotenv(ROOT / ".env")

# # ── imports ────────────────────────────────────────
# from connectors import get_connector
# from connectors.sql_connector import SQLConnector
# from extractors.schema import extract_schema
# from extractors.quality import analyze_quality
# from exporters.kg_builder import KnowledgeGraphBuilder


# # ─────────────────────────────────────────────────────────────────────────────
# # Helpers
# # ─────────────────────────────────────────────────────────────────────────────


# def load_from_json(schema_path: str):
#     """Load schema (and quality if present) from existing JSON artifacts."""
#     schema_path = Path(schema_path)
#     if not schema_path.exists():
#         raise FileNotFoundError(f"Schema JSON not found: {schema_path}")

#     with open(schema_path) as f:
#         schema = json.load(f)

#     # Try to auto-detect quality JSON sitting next to the schema file
#     quality_path = schema_path.with_name(
#         schema_path.name.replace("_schema.json", "_data_quality.json")
#     )
#     quality = None
#     if quality_path.exists():
#         with open(quality_path) as f:
#             quality = json.load(f)
#         print(f"[KG] Quality data loaded ← {quality_path.name}")
#     else:
#         print(
#             f"[KG] No quality JSON found at {quality_path.name}, skipping quality metrics."
#         )

#     return schema, quality


# def load_from_db(db_type: str) -> tuple[dict, dict | None]:
#     """Re-connect to DB and extract schema + quality on the fly."""

#     # Build connector kwargs from .env based on db_type
#     if db_type == "sqlite":
#         connector = get_connector(
#             "sqlite", filepath=os.getenv("SQLITE_FILE", "bike_store.db")
#         )
#     elif db_type == "postgresql":
#         connector = get_connector(
#             "postgresql",
#             host=os.getenv("PG_HOST", "localhost"),
#             port=int(os.getenv("PG_PORT", "5432")),
#             user=os.getenv("PG_USER"),
#             password=os.getenv("PG_PASSWORD"),
#             database=os.getenv("PG_NAME"),
#         )
#     elif db_type == "mysql":
#         connector = get_connector(
#             "mysql",
#             host=os.getenv("DB_HOST"),
#             user=os.getenv("DB_USER"),
#             password=os.getenv("DB_PASSWORD"),
#             database=os.getenv("DB_NAME"),
#         )
#     elif db_type == "mongodb":
#         connector = get_connector(
#             "mongodb",
#             uri=os.getenv("MONGO_URI"),
#             database=os.getenv("MONGO_DB"),
#         )
#     else:
#         raise ValueError(f"Unsupported db_type: {db_type}. Use --schema-json instead.")

#     with connector:
#         schema = extract_schema(connector)
#         quality = None
#         if isinstance(connector, SQLConnector):
#             print("[KG] Running quality analysis…")
#             quality = analyze_quality(connector.engine, schema)

#     return schema, quality


# # ─────────────────────────────────────────────────────────────────────────────
# # Main
# # ─────────────────────────────────────────────────────────────────────────────


# def main():
#     parser = argparse.ArgumentParser(description="Populate Neo4j KG from DB schema.")
#     parser.add_argument(
#         "--schema-json",
#         help="Path to an existing *_schema.json artifact (fastest — no DB reconnect).",
#         default=None,
#     )
#     parser.add_argument(
#         "--db",
#         help="DB type to connect to if no --schema-json given (sqlite/postgresql/mysql/mongodb).",
#         default="sqlite",
#     )
#     args = parser.parse_args()

#     # ── Load schema ───────────────────────────────────────────────────────────
#     if args.schema_json:
#         print(f"[KG] Loading schema from JSON: {args.schema_json}")
#         schema, quality = load_from_json(args.schema_json)
#         if not schema.get("database"):
#             schema["database"] = Path(args.schema_json).stem.replace("_schema", "")
#     else:
#         print(f"[KG] Connecting to {args.db} to extract schema…")
#         schema, quality = load_from_db(args.db)

#     db_name = schema.get("database", "unknown")
#     print(f"[KG] Database: {db_name}  |  Tables: {len(schema['tables'])}")

#     # ── Build graph ───────────────────────────────────────────────────────────
#     neo4j_uri = os.getenv("NEO4J_URI")
#     neo4j_user = os.getenv("NEO4J_USER")
#     neo4j_pass = os.getenv("NEO4J_PASSWORD")

#     if not all([neo4j_uri, neo4j_user, neo4j_pass]):
#         raise EnvironmentError(
#             "Missing Neo4j credentials. Set NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD in .env"
#         )

#     with KnowledgeGraphBuilder(neo4j_uri, neo4j_user, neo4j_pass) as kg:
#         kg.build(schema, quality=quality)

#     print("\n Knowledge graph populated successfully.")
#     print(f"   View it at: https://console.neo4j.io  (or http://localhost:7474/ from docker locally)")


# if __name__ == "__main__":
#     main()

"""
Populates Neo4j from an already-extracted schema.
Run AFTER app.py has generated the artifacts.

Usage
─────
    python3 scripts/build_kg.py                        
    python3 scripts/build_kg.py --schema-json artifacts/bike_store/bike_store_schema.json
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
from monitoring.sql_health import SQLHealthChecker
from exporters.kg_builder import KnowledgeGraphBuilder


def load_from_json(schema_path: str):
    schema_path = Path(schema_path)
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema JSON not found: {schema_path}")

    with open(schema_path) as f:
        schema = json.load(f)

    # Auto-detect health_deep.json sitting next to schema file
    quality_path = schema_path.with_name(
        schema_path.name.replace("_schema.json", "_health_deep.json")
    )
    quality = None
    if quality_path.exists():
        with open(quality_path) as f:
            health = json.load(f)
        quality = health.get("metrics", {}).get("tables")  # extract tables dict
        print(f"[KG] Health data loaded ← {quality_path.name}")
    else:
        print(f"[KG] No health_deep.json found, skipping quality metrics.")

    return schema, quality


def load_from_db(db_path: str):
    """Re-connect to SQLite and run health check to get quality data."""
    connector = SQLiteConnector(filepath=db_path)
    connector.connect()

    schema = connector.extract_schema()

    checker = SQLHealthChecker(connector)
    deep = checker.run_deep()
    quality = deep.metrics["tables"]

    connector.close()
    return schema, quality


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

    # Load schema + quality
    if args.schema_json:
        print(f"[KG] Loading from JSON: {args.schema_json}")
        schema, quality = load_from_json(args.schema_json)
    else:
        print(f"[KG] Connecting to: {args.db_path}")
        schema, quality = load_from_db(args.db_path)

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
        kg.build(schema, quality=quality)

    print("\nKnowledge graph populated successfully.")


if __name__ == "__main__":
    main()