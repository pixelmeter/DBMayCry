from sqlalchemy_base import SQLConnector
import urllib

class SQLServerConnector(SQLConnector):

    def _build_uri(self):
        params = urllib.parse.quote_plus(
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={self.config['host']},{self.config['port']};"
            f"DATABASE={self.config['database']};"
            f"UID={self.config['username']};"
            f"PWD={self.config['password']}"
        )

        return f"mssql+pyodbc:///?odbc_connect={params}"