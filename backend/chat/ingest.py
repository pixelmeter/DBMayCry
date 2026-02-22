"""
Run once per database after main.py generates artifacts.
Usage: uv run or python chat/ingest.py --db bike_store --artifacts-dir artifacts
"""

import argparse
import json
import os
import sys
from pathlib import Path

import chromadb

sys.path.insert(0, str(Path(__file__).parent.parent))


def load_artifact(artifacts_dir: str, db_name: str, suffix: str) -> str | None:
    # path = Path(artifacts_dir) / f"{db_name}{suffix}"
    path = Path(artifacts_dir) / db_name / f"{db_name}{suffix}"
    if not path.exists():
        print(f"  Warning: {path} not found, skipping.")
        return None
    return path.read_text()


def build_table_chunks(schema: dict, quality: dict | None, summaries: dict | None) -> list[dict]:
    """
    One chunk per table combining schema + quality + summary.
    This is the core of smart chunking — all context for a table in one place.
    """
    chunks = []

    for table_name, table in schema["tables"].items():
        lines = [f"TABLE: {table_name}"]

        # Schema
        pk = ", ".join(table["primary_key"]) or "None"
        lines.append(f"Primary Key: {pk}")

        lines.append("Columns:")
        for col in table["columns"]:
            lines.append(f"  - {col['name']} ({col['type']})")

        # Relationships
        related_tables = []
        fk_details = []
        if table["foreign_keys"]:
            lines.append("Foreign Keys:")
            for fk in table["foreign_keys"]:
                child = ", ".join(fk["column"])
                parent_table = fk["referred_table"]
                parent_col = ", ".join(fk["referred_columns"])
                lines.append(f"  - {table_name}.{child} → {parent_table}.{parent_col}")
                related_tables.append(parent_table)
                fk_details.append(f"{table_name}.{child} → {parent_table}.{parent_col}")

        # Quality
        if quality and "tables" in quality and table_name in quality["tables"]:
            tq = quality["tables"][table_name]
            lines.append(f"Row Count: {tq['row_count']}")
            low = [c for c, m in tq["columns"].items() if m["null_pct"] > 0.0]
            if low:
                lines.append(f"Incomplete columns: {', '.join(low)}")

        # AI Summary
        if summaries and table_name in summaries:
            s = summaries[table_name]
            lines.append(f"Business Description: {s.get('description', '')}")
            if s.get("data_quality_notes") and s["data_quality_notes"] != "None":
                lines.append(f"Quality Notes: {s['data_quality_notes']}")

        chunks.append({
            "content": "\n".join(lines),
            "metadata": {
                "table": table_name,
                "chunk_type": "table",
                "primary_key": pk,
                "related_to": ", ".join(related_tables) if related_tables else "none",
                "fk_details": "; ".join(fk_details) if fk_details else "none",
            }
        })

    return chunks


def build_global_context(artifacts_dir: str, db_name: str) -> str:
    """
    Pre-builds full context for global queries.
    Combines schema + summaries into one string saved as _global_context.txt.
    """
    schema_txt = load_artifact(artifacts_dir, db_name, "_llm_schema.txt") or ""
    summary_md = load_artifact(artifacts_dir, db_name, "_ai_summary.md") or ""

    context = f"=== SCHEMA ===\n{schema_txt}\n\n=== AI SUMMARIES ===\n{summary_md}"

    out_path = Path(artifacts_dir) / f"{db_name}_global_context.txt"
    out_path.write_text(context)
    print(f"  Global context → {out_path}")

    return context


def ingest(db_name: str, artifacts_dir: str):
    print(f"\nIngesting: {db_name}")
    print(f"Artifacts dir: {artifacts_dir}\n")

    # Load artifacts
    schema_json = load_artifact(artifacts_dir, db_name, "_schema.json")
    if not schema_json:
        raise FileNotFoundError(f"Schema file not found for {db_name}. Run main.py first.")

    schema = json.loads(schema_json)

    # quality_json = load_artifact(artifacts_dir, db_name, "_data_quality.json")
    quality_json = load_artifact(artifacts_dir, db_name, "_health_deep.json")
    quality = json.loads(quality_json) if quality_json else None

    summary_json = load_artifact(artifacts_dir, db_name, "_ai_summary.json")
    summaries = json.loads(summary_json) if summary_json else None

    # Build global context file
    print("Building global context...")
    build_global_context(artifacts_dir, db_name)

    # Build per-table chunks
    print("Building table chunks...")
    chunks = build_table_chunks(schema, quality, summaries)
    # print("The chunks are: ", chunks)
    print(f"  {len(chunks)} chunks built.")

    # Store in ChromaDB — one collection per DB
    chroma = chromadb.PersistentClient(path=".chromadb")

    # Delete existing collection for this DB so re-ingestion is clean
    try:
        chroma.delete_collection(db_name)
        print(f"  Cleared existing collection: {db_name}")
    except Exception:
        pass

    collection = chroma.create_collection(
        name=db_name,
        metadata={"db_name": db_name}
    )

    collection.add(
        ids=[f"{db_name}_{c['metadata']['table']}" for c in chunks],
        documents=[c["content"] for c in chunks],
        metadatas=[c["metadata"] for c in chunks],
    )

    print(f"  Stored {len(chunks)} chunks in collection '{db_name}'.")
    print(f"\nDone! '{db_name}' is ready for chat.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True, help="Database name e.g. bike_store")
    parser.add_argument("--artifacts-dir", default=".", help="Directory with generated artifacts")
    args = parser.parse_args()

    ingest(args.db, args.artifacts_dir)