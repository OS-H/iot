
from connectors.converter import Converter, abstractmethod, log


class MqttUplinkConverter(Converter):

    @abstractmethod
    def convert(self, config, data):
        pass
