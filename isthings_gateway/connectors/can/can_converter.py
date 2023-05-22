
from connectors.converter import ABC, abstractmethod


class CanConverter(ABC):
    @abstractmethod
    def convert(self, config, data):
        pass