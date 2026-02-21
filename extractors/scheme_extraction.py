from abc import ABC, abstractmethod
from model import DatabaseSchema

class BaseSchemaExtractor(ABC):

    def __init__(self, connector):
        self.connector = connector

    @abstractmethod
    def extract(self) -> DatabaseSchema:
        pass
