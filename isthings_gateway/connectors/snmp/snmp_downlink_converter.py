

from connectors.converter import Converter, log

class SNMPDownlinkConverter(Converter):
    def __init__(self, config):
        self.__config = config

    def convert(self, config, data):
        return data["params"]
