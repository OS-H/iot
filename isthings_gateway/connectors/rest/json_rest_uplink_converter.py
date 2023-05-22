

from time import time
from simplejson import dumps, loads
from connectors.rest.rest_converter import RESTConverter, log
from tb_utility.tb_utility import TBUtility


class JsonRESTUplinkConverter(RESTConverter):

    def __init__(self, config):
        self.__config = config

    def convert(self, config, data):
        datatypes = {"attributes": "attributes",
                     "timeseries": "telemetry"}
        dict_result = {"deviceName": None, "deviceType": None, "attributes": [], "telemetry": []}
        try:
            if self.__config.get("deviceNameExpression") is not None:
                dict_result["deviceName"] = TBUtility.get_value(self.__config.get("deviceNameExpression"), data, expression_instead_none=True)
            else:
                log.error("The expression for looking \"deviceName\" not found in config %s", dumps(self.__config))
            if self.__config.get("deviceTypeExpression") is not None:
                dict_result["deviceType"] = TBUtility.get_value(self.__config.get("deviceTypeExpression"), data, expression_instead_none=True)
            else:
                log.error("The expression for looking \"deviceType\" not found in config %s", dumps(self.__config))
        except Exception as e:
            log.error('Error in converter, for config: \n%s\n and message: \n%s\n', dumps(self.__config), data)
            log.exception(e)
        try:
            for datatype in datatypes:
                dict_result[datatypes[datatype]] = []
                for datatype_config in self.__config.get(datatype, []):
                    value = TBUtility.get_value(datatype_config["value"], data, datatype_config["type"], expression_instead_none=True)
                    value_tag = TBUtility.get_value(datatype_config["value"], data, datatype_config["type"], get_tag=True)
                    key = TBUtility.get_value(datatype_config["key"], data, datatype_config["type"], expression_instead_none=True)
                    key_tag = TBUtility.get_value(datatype_config["key"], data, get_tag=True)
                    if ("${" not in str(value) and "}" not in str(value)) \
                       and ("${" not in str(key) and "}" not in str(key)):
                        is_valid_key = isinstance(key, str) and "${" in datatype_config["key"] and "}" in datatype_config["key"]
                        is_valid_value = isinstance(value, str) and "${" in datatype_config["value"] and "}" in datatype_config["value"]
                        full_key = datatype_config["key"].replace('${' + key_tag + '}', key) if is_valid_key else key
                        full_value = datatype_config["value"].replace('${' + value_tag + '}', value) if is_valid_value else value
                        if datatype == 'timeseries' and (data.get("ts") is not None or data.get("timestamp") is not None):
                            dict_result[datatypes[datatype]].append({"ts": data.get('ts', data.get('timestamp', int(time()))), 'values': {full_key: full_value}})
                        else:
                            dict_result[datatypes[datatype]].append({full_key: full_value})
        except Exception as e:
            log.error('Error in converter, for config: \n%s\n and message: \n%s\n', dumps(self.__config), str(data))
            log.exception(e)
        return dict_result
