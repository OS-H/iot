
from connectors.converter import Converter, abstractmethod, log


class OpcUaConverter(Converter):
    @abstractmethod
    def convert(self, config, data):
        pass
