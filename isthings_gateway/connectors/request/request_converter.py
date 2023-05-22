

from connectors.converter import Converter, abstractmethod, log


class RequestConverter(Converter):
    @abstractmethod
    def convert(self, config, data):
        pass
