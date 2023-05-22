
from bacpypes.local.device import LocalDeviceObject
from connectors.connector import log


class TBBACnetDevice(LocalDeviceObject):
    def __init__(self, configuration):
        assert configuration is not None
        super().__init__(**configuration)
