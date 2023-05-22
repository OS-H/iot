

from connectors.converter import Converter, abstractmethod, log


class RequestUplinkConverter(Converter):

    @abstractmethod
    def convert(self, config, data):
        pass
