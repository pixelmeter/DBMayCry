from sqlalchemy import inspect
from .scheme_extraction import BaseSchemaExtractor
#  from model import ColumnSchema, TableSchema, DatabaseSchema

class SQLSchemaExtractor(BaseSchemaExtractor):
    """
    Extracts schema using SQLAlchemy Inspector and returns a normalized dict:

    {
        "database": "mydb",
        "tables": {
            "users": {
                "columns": [{"name": "...", "type": "..."}],
                "primary_key": [...],
                "foreign_keys": [
                    {
                        "column": [...],
                        "referred_table": "...",
                        "referred_columns": [...]
                    }
                ]
            }
        }
    }
    """

    def extract(self) -> dict:
        engine = self.connector.connection
        inspector = inspect(engine)

        # Detect database name safely
        database_name = (
            self.connector.config.get("database")
            or getattr(engine.url, "database", "")
        )

        schema = {
            "database": database_name,
            "tables": {}
        }

        # Optional: handle Postgres schema explicitly
        dialect = engine.dialect.name
        schema_name = "public" if dialect == "postgresql" else None

        table_names = (
            inspector.get_table_names(schema=schema_name)
            if schema_name
            else inspector.get_table_names()
        )

        for table_name in table_names:

            columns = [
                {
                    "name": col["name"],
                    "type": str(col["type"])
                }
                for col in inspector.get_columns(table_name, schema=schema_name)
            ]

            pk = inspector.get_pk_constraint(
                table_name,
                schema=schema_name
            )

            foreign_keys = [
                {
                    "column": fk["constrained_columns"],
                    "referred_table": fk["referred_table"],
                    "referred_columns": fk["referred_columns"],
                }
                for fk in inspector.get_foreign_keys(
                    table_name,
                    schema=schema_name
                )
            ]

            schema["tables"][table_name] = {
                "columns": columns,
                "primary_key": pk.get("constrained_columns", []),
                "foreign_keys": foreign_keys,
            }

        return schema


class MySQLSchemaExtractor(SQLSchemaExtractor):
    pass


class SQLServerSchemaExtractor(SQLSchemaExtractor):
    pass


class SQLiteSchemaExtractor(SQLSchemaExtractor):
    pass


