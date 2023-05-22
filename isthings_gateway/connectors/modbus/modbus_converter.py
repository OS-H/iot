
from connectors.converter import Converter, abstractmethod, log


class ModbusConverter(Converter):
    @abstractmethod
    def convert(self, config, data):
        pass
