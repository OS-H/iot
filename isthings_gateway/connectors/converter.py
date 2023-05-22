
import logging
from abc import ABC, abstractmethod

log = logging.getLogger("converter")


class Converter(ABC):

    @abstractmethod
    def convert(self, config, data):
        pass
