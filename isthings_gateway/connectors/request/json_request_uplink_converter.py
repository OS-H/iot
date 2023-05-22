

from simplejson import dumps, loads
from connectors.request.request_converter import RequestConverter, log
from tb_utility.tb_utility import TBUtility


class JsonRequestUplinkConverter(RequestConverter):
    def __init__(self, config):
        self.__config = config
        self.__datatypes = {"attributes": "attributes",
                            "telemetry": "telemetry"}

    def convert(self, config, data):
        if isinstance(data, (bytes, str)):
            data = loads(data)
        dict_result = {"deviceName": None, "deviceType": None, "attributes": [], "telemetry": []}
        try:
            if self.__config['converter'].get("deviceNameJsonExpression") is not None:
                dict_result["deviceName"] = TBUtility.get_value(self.__config['converter'].get("deviceNameJsonExpression"), data, expression_instead_none=True)
            else:
                log.error("The expression for looking \"deviceName\" not found in config %s", dumps(self.__config['converter']))
            if self.__config['converter'].get("deviceTypeJsonExpression") is not None:
                dict_result["deviceType"] = TBUtility.get_value(self.__config['converter'].get("deviceTypeJsonExpression"), data, expression_instead_none=True)
            else:
                log.error("The expression for looking \"deviceType\" not found in config %s", dumps(self.__config['converter']))
        except Exception as e:
            log.exception(e)

        try:
            for datatype in self.__datatypes:
                current_datatype = self.__datatypes[datatype]
                for datatype_object_config in self.__config["converter"].get(datatype, []):
                    datatype_object_config_key = TBUtility.get_value(datatype_object_config["key"], data, datatype_object_config["type"], expression_instead_none=True)
                    datatype_object_config_value = TBUtility.get_value(datatype_object_config["value"], data, datatype_object_config["type"])
                    if datatype_object_config_key is not None and datatype_object_config_value is not None:
                        dict_result[current_datatype].append({datatype_object_config_key: datatype_object_config_value})
                    else:
                        error_string = "Cannot find the key in the input data" if datatype_object_config_key is None else "Cannot find the value from the input data"
                        log.error(error_string)
        except Exception as e:
            log.exception(e)

        return dict_result
