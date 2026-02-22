# extractors/factory.py

from extractors.sql_extractor import SQLSchemaExtractor
from mongo_extractor import MongoSchemaExtractor

class ExtractorFactory:

    REGISTRY = {
        "sqlite": SQLSchemaExtractor,
        "mysql": SQLSchemaExtractor,
        "sqlserver": SQLSchemaExtractor,
        "postgres": SQLSchemaExtractor,
        "mongo": MongoSchemaExtractor,
    }

    @classmethod
    def create(cls, db_type: str, connector):
        extractor_class = cls.REGISTRY.get(db_type.lower())
        if not extractor_class:
            raise ValueError(f"No extractor for {db_type}")
        return extractor_class(connector)