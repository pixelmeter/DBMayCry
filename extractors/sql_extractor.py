from sqlalchemy import inspect
from scheme_extraction import BaseSchemaExtractor
from model import ColumnSchema, TableSchema, DatabaseSchema

class SQLSchemaExtractor(BaseSchemaExtractor):

    def extract(self) -> DatabaseSchema:
        engine = self.connector.connection
        inspector = inspect(engine)
        tables = []

        for table_name in inspector.get_table_names():
            columns = []
            pk_columns = inspector.get_pk_constraint(table_name).get("constrained_columns", [])
            fks = inspector.get_foreign_keys(table_name)

            fk_map = {}
            for fk in fks:
                for col in fk["constrained_columns"]:
                    fk_map[col] = f"{fk['referred_table']}"

            for column in inspector.get_columns(table_name):
                columns.append(
                    ColumnSchema(
                        name=column["name"],
                        dtype=str(column["type"]),
                        nullable=column["nullable"],
                        primary_key=column["name"] in pk_columns,
                        foreign_key=fk_map.get(column["name"])
                    )
                )

            tables.append(TableSchema(name=table_name, columns=columns))

        return DatabaseSchema(
            database=self.connector.config.get("database", "unknown"),
            tables=tables
        )


class MySQLSchemaExtractor(SQLSchemaExtractor):
    pass

class SQLServerSchemaExtractor(SQLSchemaExtractor):
    pass

class SQLiteSchemaExtractor(SQLSchemaExtractor):
    pass