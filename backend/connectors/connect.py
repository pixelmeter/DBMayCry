# DBS - SQL , PSQL, MONGO, REDIS, CASSANDRA, SNOFLAKE, ARORA
from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseConnector(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connection = None

    @abstractmethod
    def connect(self) -> None:
        pass

    @abstractmethod
    def disconnect(self) -> None:
        pass

    @abstractmethod
    def run(self, query: str, **kwargs) -> None:
        pass

    @abstractmethod
    def test_connection(self) -> None:
        pass