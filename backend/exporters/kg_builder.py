"""
Converts the schema dict into a deterministic Neo4j property graph using pure Cypher.

Node labels
───────────
  (:Database)   – one per run
  (:Table)      – one per table / collection
  (:Column)     – one per column

Relationship types
──────────────────
  (:Database)  -[:HAS_TABLE]->   (:Table)
  (:Table)     -[:HAS_COLUMN]->  (:Column)
  (:Table)     -[:RELATES_TO  { via_column, referred_column }]-> (:Table)
  (:Column)    -[:IS_PK_OF]->    (:Table)
  (:Column)    -[:IS_FK_TO  { referred_column }]-> (:Table)

Usage
─────
    from exporters.kg_builder import KnowledgeGraphBuilder

    with KnowledgeGraphBuilder(uri, user, password) as kg:
        kg.build(schema)
"""

from __future__ import annotations
from neo4j import GraphDatabase


# ─────────────────────────────────────────────────────────────────────────────
# Cypher templates
# ─────────────────────────────────────────────────────────────────────────────

_MERGE_DB = """
MERGE (db:Database {name: $db_name})
SET db.updated_at = timestamp()
"""

_MERGE_TABLE = """
MERGE (t:Table {fqn: $fqn})
SET t.name      = $table_name,
    t.database  = $db_name,
    t.pk        = $pk
"""

_LINK_DB_TABLE = """
MATCH (db:Database {name: $db_name})
MATCH (t:Table     {fqn: $fqn})
MERGE (db)-[:HAS_TABLE]->(t)
"""

_MERGE_COLUMN = """
MERGE (c:Column {fqn: $col_fqn})
SET c.name      = $col_name,
    c.type      = $col_type,
    c.table_fqn = $table_fqn,
    c.is_pk     = $is_pk
"""

_LINK_TABLE_COLUMN = """
MATCH (t:Table  {fqn: $table_fqn})
MATCH (c:Column {fqn: $col_fqn})
MERGE (t)-[:HAS_COLUMN]->(c)
"""

_LINK_PK = """
MATCH (c:Column {fqn: $col_fqn})
MATCH (t:Table  {fqn: $table_fqn})
MERGE (c)-[:IS_PK_OF]->(t)
"""

_LINK_FK_TABLE = """
MATCH (from_t:Table {fqn: $from_fqn})
MATCH (to_t:Table   {fqn: $to_fqn})
MERGE (from_t)-[r:RELATES_TO {via_column: $via_col}]->(to_t)
SET r.referred_column = $ref_col
"""

_LINK_FK_COLUMN = """
MATCH (fk_col:Column {fqn: $fk_col_fqn})
MATCH (ref_t:Table   {fqn: $ref_table_fqn})
MERGE (fk_col)-[r:IS_FK_TO {referred_column: $ref_col}]->(ref_t)
"""


# ─────────────────────────────────────────────────────────────────────────────
# Builder
# ─────────────────────────────────────────────────────────────────────────────


class KnowledgeGraphBuilder:
    """
    Idempotent graph builder — safe to re-run after schema changes.
    All MERGE statements ensure no duplicates are created.
    Stores schema structure and FK relationships only.
    """

    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str):
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

    def build(self, schema: dict) -> None:
        """
        Builds the knowledge graph from schema dict.
        schema – dict returned by connector.extract_schema()
        """
        db_name = schema["database"]

        with self.driver.session() as session:
            print(f"[KG] Building graph for database: {db_name}")

            # 1. Database node
            session.run(_MERGE_DB, db_name=db_name)

            for table_name, table in schema["tables"].items():
                fqn = f"{db_name}.{table_name}"
                pk_cols = table["primary_key"]

                # 2. Table node
                session.run(
                    _MERGE_TABLE,
                    fqn=fqn,
                    table_name=table_name,
                    db_name=db_name,
                    pk=pk_cols,
                )
                session.run(_LINK_DB_TABLE, db_name=db_name, fqn=fqn)

                # 3. Column nodes
                for col in table["columns"]:
                    col_fqn = f"{fqn}.{col['name']}"
                    is_pk = col["name"] in pk_cols

                    session.run(
                        _MERGE_COLUMN,
                        col_fqn=col_fqn,
                        col_name=col["name"],
                        col_type=col["type"],
                        table_fqn=fqn,
                        is_pk=is_pk,
                    )
                    session.run(_LINK_TABLE_COLUMN, table_fqn=fqn, col_fqn=col_fqn)

                    if is_pk:
                        session.run(_LINK_PK, col_fqn=col_fqn, table_fqn=fqn)

                # 4. Foreign-key relationships
                for fk in table["foreign_keys"]:
                    ref_table_fqn = f"{db_name}.{fk['referred_table']}"
                    via_col = ", ".join(fk["column"])
                    ref_col = ", ".join(fk["referred_columns"])

                    # Table → Table edge (high-level graph traversal)
                    session.run(
                        _LINK_FK_TABLE,
                        from_fqn=fqn,
                        to_fqn=ref_table_fqn,
                        via_col=via_col,
                        ref_col=ref_col,
                    )

                    # Column → Table edge (column-level lineage)
                    for fk_col_name, ref_col_name in zip(
                        fk["column"], fk["referred_columns"]
                    ):
                        session.run(
                            _LINK_FK_COLUMN,
                            fk_col_fqn=f"{fqn}.{fk_col_name}",
                            ref_table_fqn=ref_table_fqn,
                            ref_col=ref_col_name,
                        )

                print(f"  [KG] ✓ {table_name}")

        print(f"[KG] Graph built → {db_name}")

    def close(self):
        self.driver.close()
        print("[KG] Neo4j connection closed.")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()