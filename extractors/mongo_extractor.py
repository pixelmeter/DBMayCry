from scheme_extraction import BaseSchemaExtractor
from model import ColumnSchema, TableSchema, DatabaseSchema

class MongoSchemaExtractor(BaseSchemaExtractor):

    def extract(self) -> DatabaseSchema:
        db = self.connector.connection[self.connector.config["database"]]

        tables = []

        for collection_name in db.list_collection_names():
            sample = db[collection_name].find_one()

            columns = []
            if sample:
                for key, value in sample.items():
                    columns.append(
                        ColumnSchema(
                            name=key,
                            dtype=type(value).__name__,
                            nullable=True,
                            primary_key=(key == "_id")
                        )
                    )

            tables.append(TableSchema(name=collection_name, columns=columns))

        return DatabaseSchema(
            database=self.connector.config["database"],
            tables=tables
        )