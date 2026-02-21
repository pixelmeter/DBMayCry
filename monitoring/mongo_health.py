import time
from .health_checker import BaseHealthChecker

class MongoHealthChecker(BaseHealthChecker):
    def run(self):
        report = {}

        start = time.time()
        try: 
            self.connector.test_connection()
        except Exception:
            report['status'] = "not healthy"
            raise Exception
        latency = (time.time() - start) * 1000

        report["latency_ms"] = round(latency, 2)
        report['status'] = "healthy"

        server_status = self.connector.connection.admin.command("serverStatus")
        connections = server_status['connections']

        report["active_connections"] = connections['active']
        return report