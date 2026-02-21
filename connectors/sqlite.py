from .sqlalchemy_base import SQLConnector
from sqlalchemy import create_engine, inspect, text
import os
import re
from typing import Dict, Any


class SQLiteConnector:
    """
    SQLite connector supporting:

    - Direct .db file connection
    - Query execution
    - Schema extraction via Inspector
    - Schema parsing from .sql file
    - Dump file loading
    """

    def __init__(self, filepath: str = None, uri: str = None):
        self.filepath = filepath
        self.uri = uri
        self.engine = None
        self.inspector = None

    # --------------------------------------------------
    # CONNECTION
    # --------------------------------------------------
    def connect(self):
        if self.uri:
            url = self.uri
        elif self.filepath:
            url = f"sqlite:///{self.filepath}"
        else:
            raise ValueError("Either filepath or uri must be provided")

        self.engine = create_engine(url)
        self.inspector = inspect(self.engine)

        print(f"[SQLITE] Connected → {url}")

    def close(self):
        if self.engine:
            self.engine.dispose()
            print("[SQLITE] Connection closed.")

    # --------------------------------------------------
    # QUERY EXECUTION
    # --------------------------------------------------
    def run(self, query: str, **params):
        if not self.engine:
            raise RuntimeError("Database not connected")

        with self.engine.connect() as conn:
            result = conn.execute(text(query), params)
            return result.fetchall()

    # --------------------------------------------------
    # SCHEMA EXTRACTION (Live DB)
    # --------------------------------------------------
    def extract_schema(self) -> Dict[str, Any]:
        if not self.inspector:
            raise RuntimeError("Database not connected")

        schema = {
            "database": self.engine.url.database,
            "tables": {}
        }

        for table_name in self.inspector.get_table_names():

            columns = [
                {
                    "name": col["name"],
                    "type": str(col["type"])
                }
                for col in self.inspector.get_columns(table_name)
            ]

            pk = self.inspector.get_pk_constraint(table_name)

            foreign_keys = [
                {
                    "column": fk["constrained_columns"],
                    "referred_table": fk["referred_table"],
                    "referred_columns": fk["referred_columns"],
                }
                for fk in self.inspector.get_foreign_keys(table_name)
            ]

            schema["tables"][table_name] = {
                "columns": columns,
                "primary_key": pk.get("constrained_columns", []),
                "foreign_keys": foreign_keys,
            }

        return schema

    # --------------------------------------------------
    # LOAD SCHEMA FROM .SQL FILE (DDL only)
    # --------------------------------------------------
    def parse_schema_file(self, filepath: str) -> Dict[str, Any]:
        if not os.path.exists(filepath):
            raise FileNotFoundError(filepath)

        with open(filepath, "r") as f:
            sql = f.read()

        schema = {
            "database": "schema_file_import",
            "tables": {}
        }

        table_blocks = re.findall(
            r"CREATE TABLE\s+(\w+)\s*\((.*?)\);",
            sql,
            re.DOTALL | re.IGNORECASE
        )

        for table_name, body in table_blocks:

            columns = []
            primary_key = []
            foreign_keys = []

            lines = body.split(",")

            for line in lines:
                line = line.strip()

                if line.upper().startswith("PRIMARY KEY"):
                    pk_cols = re.findall(r"\((.*?)\)", line)
                    if pk_cols:
                        primary_key = [c.strip() for c in pk_cols[0].split(",")]

                elif line.upper().startswith("FOREIGN KEY"):
                    fk_cols = re.findall(r"\((.*?)\)", line)
                    ref = re.search(
                        r"REFERENCES\s+(\w+)\s*\((.*?)\)",
                        line,
                        re.IGNORECASE
                    )

                    if fk_cols and ref:
                        foreign_keys.append({
                            "column": [c.strip() for c in fk_cols[0].split(",")],
                            "referred_table": ref.group(1),
                            "referred_columns": [
                                c.strip() for c in ref.group(2).split(",")
                            ]
                        })

                else:
                    parts = line.split()
                    if len(parts) >= 2:
                        columns.append({
                            "name": parts[0],
                            "type": parts[1]
                        })

            schema["tables"][table_name] = {
                "columns": columns,
                "primary_key": primary_key,
                "foreign_keys": foreign_keys
            }

        return schema

    # --------------------------------------------------
    # LOAD FULL .SQL DUMP INTO TEMP DB
    # --------------------------------------------------
    def load_dump_file(self, filepath: str) -> Dict[str, Any]:
        if not os.path.exists(filepath):
            raise FileNotFoundError(filepath)

        temp_engine = create_engine("sqlite:///:memory:")
        conn = temp_engine.connect()

        with open(filepath, "r") as f:
            dump_sql = f.read()

        conn.exec_driver_sql(dump_sql)

        inspector = inspect(temp_engine)

        schema = {
            "database": "dump_import",
            "tables": {}
        }

        for table_name in inspector.get_table_names():

            columns = [
                {
                    "name": col["name"],
                    "type": str(col["type"])
                }
                for col in inspector.get_columns(table_name)
            ]

            pk = inspector.get_pk_constraint(table_name)

            foreign_keys = [
                {
                    "column": fk["constrained_columns"],
                    "referred_table": fk["referred_table"],
                    "referred_columns": fk["referred_columns"],
                }
                for fk in inspector.get_foreign_keys(table_name)
            ]

            schema["tables"][table_name] = {
                "columns": columns,
                "primary_key": pk.get("constrained_columns", []),
                "foreign_keys": foreign_keys,
            }

        conn.close()
        temp_engine.dispose()

        return schema