
from re import fullmatch

from connectors.opcua.opcua_converter import OpcUaConverter, log
from tb_utility.tb_utility import TBUtility


class OpcUaUplinkConverter(OpcUaConverter):
    def __init__(self, config):
        self.__config = config

    def convert(self, config, data):
        device_name = self.__config["deviceName"]
        result = {"deviceName": device_name,
                  "deviceType": self.__config.get("deviceType", "OPC-UA Device"),
                  "attributes": [],
                  "telemetry": [], }
        try:
            information_types = {"attributes": "attributes", "timeseries": "telemetry"}
            for information_type in information_types:
                for information in self.__config[information_type]:
                    path = TBUtility.get_value(information["path"], get_tag=True)
                    if isinstance(config, tuple):
                        config_information = config[0].replace('\\\\', '\\') if path == config[0].replace('\\\\', '\\') or fullmatch(path, config[0].replace('\\\\', '\\')) else config[1].replace('\\\\', '\\')
                    else:
                        config_information = config.replace('\\\\', '\\')
                    if path == config_information or fullmatch(path, config_information) or path.replace('\\\\', '\\') == config_information:
                        result[information_types[information_type]].append({information["key"]: information["path"].replace("${"+path+"}", str(data))})
            return result
        except Exception as e:
            log.exception(e)
