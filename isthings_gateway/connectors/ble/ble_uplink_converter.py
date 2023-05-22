
from connectors.converter import Converter, log, abstractmethod


class BLEUplinkConverter(Converter):

    @abstractmethod
    def convert(self, config, data):
        pass
