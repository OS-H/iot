

from connectors.converter import Converter, log

class SNMPUplinkConverter(Converter):
    def __init__(self, config):
        self.__config = config

    def convert(self, config, data):
        result = {
            "deviceName": self.__config["deviceName"],
            "deviceType": self.__config["deviceType"],
            "attributes": [],
            "telemetry": []
        }
        try:
            if isinstance(data, dict):
                result[config[0]].append({config[1]["key"]: {str(k): str(v) for k, v in data.items()}})
            elif isinstance(data, list):
                if isinstance(data[0], str):
                    result[config[0]].append({config[1]["key"]: ','.join(data)})
                elif isinstance(data[0], dict):
                    res = {}
                    for item in data:
                        res.update(**item)
                    result[config[0]].append({config[1]["key"]: {str(k): str(v) for k, v in res.items()}})
            elif isinstance(data, str):
                result[config[0]].append({config[1]["key"]: data})
            elif isinstance(data, bytes):
                result[config[0]].append({config[1]["key"]: data.decode("UTF-8")})
            log.debug(result)
        except Exception as e:
            log.exception(e)
        return result
