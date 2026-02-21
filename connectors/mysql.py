from .sqlalchemy_base import SQLConnector

class MySQLConnector(SQLConnector):

    def _build_uri(self):
        return (
            f"mysql+pymysql://{self.config['username']}:{self.config['password']}"
            f"@{self.config['host']}:{self.config['port']}/{self.config['database']}"
        )