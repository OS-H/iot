

from simplejson import dumps
from connectors.request.request_converter import RequestConverter, log


class JsonRequestDownlinkConverter(RequestConverter):
    def __init__(self, config):
        self.__config = config

    def convert(self, config, data):
        try:
            if data["data"].get("id") is None:
                attribute_key = list(data["data"].keys())[0]
                attribute_value = list(data["data"].values())[0]

                result = {"url": self.__config["requestUrlExpression"].replace("${attributeKey}", attribute_key)\
                                                                      .replace("${attributeValue}", attribute_value)\
                                                                      .replace("${deviceName}", data["device"]),
                          "data": self.__config["valueExpression"].replace("${attributeKey}", attribute_key)\
                                                                  .replace("${attributeValue}", attribute_value)\
                                                                  .replace("${deviceName}", data["device"])}
            else:
                request_id = str(data["data"]["id"])
                method_name = data["data"]["method"]
                params = dumps(data["data"]["params"]) or str(data["data"]["params"])

                result = {"url": self.__config["requestUrlExpression"].replace("${requestId}", request_id)\
                                                                      .replace("${methodName}", method_name)\
                                                                      .replace("${params}", params)\
                                                                      .replace("${deviceName}", data["device"]),
                          "data": self.__config["valueExpression"].replace("${requestId}", request_id)\
                                                                  .replace("${methodName}", method_name)\
                                                                  .replace("${params}", params)\
                                                                  .replace("${deviceName}", data["device"])}
            return result
        except Exception as e:
            log.exception(e)
