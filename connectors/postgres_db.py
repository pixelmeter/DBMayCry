from .sqlalchemy_base import SQLConnector

class PostGresConnector(SQLConnector):
    def _build_uri(self):
        return (
            f"postgresql://{self.config['username']}:{self.config['password']}"
            f"@{self.config['host']}:{self.config['port']}/{self.config['database']}"
        )