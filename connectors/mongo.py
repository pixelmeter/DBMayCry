from .connect import BaseConnector
from pymongo import MongoClient
import json

class MongoConnector(BaseConnector):
    def connect(self):
        self.connection = MongoClient(self.config["uri"])
    
    def disconnect(self):
        if self.connection:
            self.connection.close()
    
    def run(self, query: str, collection: str):
        try:
            qurey_str = json.load(query)
        except json.JSONDecodeError as e:
            raise e

        return list[self.connection[self.config['database']][collection].find(qurey_str)]
    
    def test_connection(self):
        try:
            self.connection.admin.ping("ping")
            return True
        except Exception:
            return False