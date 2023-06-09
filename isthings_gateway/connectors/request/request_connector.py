

from threading import Thread
from queue import Queue
from random import choice
from string import ascii_lowercase
from time import sleep, time
from re import fullmatch

from tb_utility.tb_utility import TBUtility

try:
    from requests import Timeout, request
except ImportError:
    print("Requests library not found - installing...")
    TBUtility.install_package("requests")
    from requests import Timeout, request
import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import RequestException

from connectors.connector import Connector, log
from connectors.request.json_request_uplink_converter import JsonRequestUplinkConverter
from connectors.request.json_request_downlink_converter import JsonRequestDownlinkConverter

# pylint: disable=E1101
requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += ':ADH-AES128-SHA256'


class RequestConnector(Connector, Thread):
    def __init__(self, gateway, config, connector_type):
        super().__init__()
        self.statistics = {'MessagesReceived': 0,
                           'MessagesSent': 0}
        self.__rpc_requests = []
        self.__config = config
        self.__connector_type = connector_type
        self.__gateway = gateway
        self.__security = HTTPBasicAuth(self.__config["security"]["username"], self.__config["security"]["password"]) if \
        self.__config["security"]["type"] == "basic" else None
        self.__host = None
        self.__service_headers = {}
        if "http://" in self.__config["host"].lower() or "https://" in self.__config["host"].lower():
            self.__host = self.__config["host"]
        else:
            self.__host = "http://" + self.__config["host"]
        self.__ssl_verify = self.__config.get("SSLVerify", False)
        self.setName(self.__config.get("name", "".join(choice(ascii_lowercase) for _ in range(5))))
        self.daemon = True
        self.__connected = False
        self.__stopped = False
        self.__requests_in_progress = []
        self.__convert_queue = Queue(1000000)
        self.__attribute_updates = []
        self.__fill_attribute_updates()
        self.__fill_rpc_requests()
        self.__fill_requests()

    def run(self):
        while not self.__stopped:
            if self.__requests_in_progress:
                for request in self.__requests_in_progress:
                    if time() >= request["next_time"]:
                        thread = Thread(target=self.__send_request, args=(request, self.__convert_queue, log),
                                        daemon=True,
                                        name="Request to endpoint \'%s\' Thread" % (request["config"].get("url")))
                        thread.start()
            else:
                sleep(.1)
            self.__process_data()

    def on_attributes_update(self, content):
        try:
            for attribute_request in self.__attribute_updates:
                if fullmatch(attribute_request["deviceNameFilter"], content["device"]) and fullmatch(
                        attribute_request["attributeFilter"], list(content["data"].keys())[0]):
                    converted_data = attribute_request["converter"].convert(attribute_request, content)
                    response_queue = Queue(1)
                    request_dict = {"config": {**attribute_request,
                                               **converted_data},
                                    "request": request}
                    attribute_update_request_thread = Thread(target=self.__send_request,
                                                             args=(request_dict, response_queue, log),
                                                             daemon=True,
                                                             name="Attribute request to %s" % (converted_data["url"]))
                    attribute_update_request_thread.start()
                    attribute_update_request_thread.join()
                    if not response_queue.empty():
                        response = response_queue.get_nowait()
                        log.debug(response)
                    del response_queue
        except Exception as e:
            log.exception(e)

    def server_side_rpc_handler(self, content):
        try:
            for rpc_request in self.__rpc_requests:
                if fullmatch(rpc_request["deviceNameFilter"], content["device"]) and fullmatch(
                        rpc_request["methodFilter"], content["data"]["method"]):
                    converted_data = rpc_request["converter"].convert(rpc_request, content)
                    response_queue = Queue(1)
                    request_dict = {"config": {**rpc_request,
                                               **converted_data},
                                    "request": request}
                    request_dict["config"].get("uplink_converter")
                    rpc_request_thread = Thread(target=self.__send_request,
                                                args=(request_dict, response_queue, log),
                                                daemon=True,
                                                name="RPC request to %s" % (converted_data["url"]))
                    rpc_request_thread.start()
                    rpc_request_thread.join()
                    if not response_queue.empty():
                        response = response_queue.get_nowait()
                        log.debug(response)
                        self.__gateway.send_rpc_reply(device=content["device"], req_id=content["data"]["id"],
                                                      content=response[2])
                    self.__gateway.send_rpc_reply(success_sent=True)

                    del response_queue
        except Exception as e:
            log.exception(e)

    def __fill_requests(self):
        log.debug(self.__config["mapping"])
        for endpoint in self.__config["mapping"]:
            try:
                log.debug(endpoint)
                converter = None
                if endpoint["converter"]["type"] == "custom":
                    module = TBUtility.check_and_import(self.__connector_type, endpoint["converter"]["extension"])
                    if module is not None:
                        log.debug('Custom converter for url %s - found!', endpoint["url"])
                        converter = module(endpoint)
                    else:
                        log.error("\n\nCannot find extension module for %s url.\nPlease check your configuration.\n",
                                  endpoint["url"])
                else:
                    converter = JsonRequestUplinkConverter(endpoint)
                self.__requests_in_progress.append({"config": endpoint,
                                                    "converter": converter,
                                                    "next_time": time(),
                                                    "request": request})
            except Exception as e:
                log.exception(e)

    def __fill_attribute_updates(self):
        for attribute_request in self.__config.get("attributeUpdates", []):
            if attribute_request.get("converter") is not None:
                converter = TBUtility.check_and_import("request", attribute_request["converter"])(attribute_request)
            else:
                converter = JsonRequestDownlinkConverter(attribute_request)
            attribute_request_dict = {**attribute_request, "converter": converter}
            self.__attribute_updates.append(attribute_request_dict)

    def __fill_rpc_requests(self):
        for rpc_request in self.__config.get("serverSideRpc", []):
            if rpc_request.get("converter") is not None:
                converter = TBUtility.check_and_import("request", rpc_request["converter"])(rpc_request)
            else:
                converter = JsonRequestDownlinkConverter(rpc_request)
            rpc_request_dict = {**rpc_request, "converter": converter}
            self.__rpc_requests.append(rpc_request_dict)

    def __send_request(self, request, converter_queue, logger):
        url = ""
        try:
            request["next_time"] = time() + request["config"].get("scanPeriod", 10)
            request_url_from_config = request["config"]["url"]
            request_url_from_config = str('/' + request_url_from_config) if request_url_from_config[
                                                                                0] != '/' else request_url_from_config
            logger.debug(request_url_from_config)
            url = self.__host + request_url_from_config
            logger.debug(url)
            request_timeout = request["config"].get("timeout", 1)
            params = {
                "method": request["config"].get("httpMethod", "GET"),
                "url": url,
                "timeout": request_timeout,
                "allow_redirects": request["config"].get("allowRedirects", False),
                "verify": self.__ssl_verify,
                "auth": self.__security
            }
            if request["config"].get("httpHeaders") is not None:
                params["headers"] = request["config"]["httpHeaders"]
            if request["config"].get("payload") is not None:
                params["data"] = request["config"]["payload"]
            response = request["request"](**params)
            logger.info("response:"+repr(response))
            if response and response.ok:
                if not converter_queue.full():
                    data_to_storage = [url, request["converter"]]
                    try:
                        data_to_storage.append(response.json())
                    except:
                        data_to_storage.append(response.text)
                    if len(data_to_storage) == 3:
                        converter_queue.put(data_to_storage)
                        self.statistics["MessagesReceived"] = self.statistics["MessagesReceived"] + 1
            else:
                logger.error("Request to URL: %s finished with code: %i", url, response.status_code)
        except Timeout:
            logger.error("Timeout error on request %s.", url)
        except RequestException as e:
            logger.error("Cannot connect to %s. Connection error.", url)
            logger.debug(e)
        except ConnectionError:
            logger.error("Cannot connect to %s. Connection error.", url)
        except Exception as e:
            logger.exception(e)

    def __process_data(self):
        try:
            if not self.__convert_queue.empty():
                url, converter, data = self.__convert_queue.get()
                data_to_send = {}
                if isinstance(data, list):
                    for data_item in data:
                        converted_data = converter.convert(url, data_item)
                        if data_to_send.get(converted_data["deviceName"]) is None:
                            data_to_send[converted_data["deviceName"]] = converted_data
                        else:
                            if converted_data["telemetry"]:
                                data_to_send[converted_data["deviceName"]]["telemetry"].append(
                                    converted_data["telemetry"][0])
                            if converted_data["attributes"]:
                                data_to_send[converted_data["deviceName"]]["attributes"].append(
                                    converted_data["attributes"][0])
                    for device in data_to_send:
                        self.__gateway.send_to_storage(self.get_name(), data_to_send[device])
                        self.statistics["MessagesSent"] = self.statistics["MessagesSent"] + 1
                    log.debug(data_to_send)
                else:
                    data_to_send = converter.convert(url, data)
                    self.__gateway.send_to_storage(self.get_name(), data_to_send)
                    self.statistics["MessagesSent"] = self.statistics["MessagesSent"] + 1
                log.debug(data_to_send)
            else:
                sleep(.01)
        except Exception as e:
            log.exception(e)

    def get_name(self):
        return self.name

    def is_connected(self):
        return self.__connected

    def open(self):
        self.__stopped = False
        self.start()

    def close(self):
        self.__stopped = True
