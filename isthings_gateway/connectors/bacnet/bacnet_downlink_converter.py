
from connectors.bacnet.bacnet_converter import Converter, log

class BACnetDownlinkConverter(Converter):
    def __init__(self, config):
        self.__config = config

    def convert(self, config, data):
        log.debug(config, data)