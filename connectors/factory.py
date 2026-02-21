from postgres import PostGresConnector
from mongo import MongoConnector
from sqlite import SQLiteConnector
from mysql import MySQLConnector
from sqlserver import SQLServerConnector


class ConnectionFactory:
    REG = {
        "postgres": PostGresConnector,
        "mongo": MongoConnector,
        "mysql": MySQLConnector,
        "sqlite": SQLiteConnector,
        "sqlserver": SQLServerConnector
    }

    @classmethod
    def create(cls, db_type: str, config: dict):
        connector_class = cls.REG.get(db_type.lower())
        if not connector_class:
            raise ValueError(f"Unsupported database type: {db_type}")
        return connector_class(config)