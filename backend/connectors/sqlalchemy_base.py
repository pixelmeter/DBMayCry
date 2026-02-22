from .connect import BaseConnector
from sqlalchemy import create_engine, text

class SQLConnector(BaseConnector):
    def connect(self):
        if self.config.get("uri"):
            uri = self.config['uri']
        else:
            uri = self._build_uri()
        self.connection = create_engine(uri)

    def run(self, query, **kwargs):
        with self.connection.connect() as conn:
            result = conn.execute(text(query), kwargs)
            return result.fetchall()

    def test_connection(self):
        try:
            self.run("SELECT 1")
            return True
        except Exception:
            return False

    def disconnect(self):
        if self.connection:
            self.connection.dispose()

    def _build_uri(self):
        # TODO - Write this function
        raise NotImplementedError