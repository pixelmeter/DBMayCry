from .sqlalchemy_base import SQLConnector

class SQLiteConnector(SQLConnector):

    def _build_uri(self):
        db_path = self.config["database"]
        return f"sqlite:///{db_path}"