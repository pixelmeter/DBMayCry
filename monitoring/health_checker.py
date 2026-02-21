from abc import ABC, abstractmethod
class BaseHealthChecker(ABC):

    def __init__(self, connector):
        self.connector = connector

    @abstractmethod
    def run_light(self):
        pass

    @abstractmethod
    def run_deep(self):
        pass