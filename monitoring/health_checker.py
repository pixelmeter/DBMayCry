from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseHealthChecker(ABC):

    def __init__(self, connector):
        self.connector = connector

    @abstractmethod
    def run(self) -> Dict[str, Any]:
        pass