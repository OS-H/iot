from ctypes import cdll
from importlib.abc import InspectLoader
from math import gamma
from os import remove, linesep, stat
from os.path import exists, dirname
from re import findall
from threading import Thread
from time import time, sleep
from logging import getLogger
from logging.config import fileConfig
from base64 import b64encode, b64decode
from simplejson import dumps, loads, dump, load
from yaml import safe_dump
from configparser import ConfigParser
from copy import deepcopy

from tb_utility.tb_utility import TBUtility
from gateway.tb_logger import TBLoggerHandler

# pylint: disable=protected-access
LOG = getLogger("service")


class UpdateConfigurator:
    def __init__(self, gateway, config):
        self.__gateway = gateway
        self.__old_connectors_configs = self.__load_connectors_config(config)
        self.in_process = False

    def process_config(self, configuration):
        try:
            if not self.in_process:
                self.in_process = True
                LOG.debug('Process configuration start.')
                add_configs,del_configs= self.__check_connectors_config(configuration)
                if del_configs:
                    for config_name in del_configs:
                        self.__del_connector(del_configs[config_name]["type"],config_name)
                        LOG.info("Remove configuration: %s",config_name)
                    sleep(1)
                if add_configs:
                    for config_name in add_configs:
                        self.__add_connector(add_configs[config_name],add_configs[config_name]["type"],config_name)
                        LOG.info("Add configuration: %s",config_name)
                self.in_process = False
            else:
                LOG.error("Update configuration is already in processing.")
                return False
        except Exception as e:
            self.in_process = False
            LOG.exception(e)

    def __check_connectors_config(self,configuration):
        new_configs = self.__load_connectors_config(configuration)
        buf = deepcopy(new_configs)
        del_configs={}
        for config in self.__old_connectors_configs:
            if config in new_configs:
                if new_configs[config]['mtime'] and new_configs[config]['mtime']!=self.__old_connectors_configs[config]['mtime']:
                    del_configs[config]=self.__old_connectors_configs[config]
                else:
                    del new_configs[config]
            else:
                del_configs[config]=self.__old_connectors_configs[config]
        self.__old_connectors_configs = buf
        return new_configs, del_configs
    
    def __load_connectors_config(self,gw_configuration):
        if gw_configuration.get("connectors"):
            connectors_configs={}
            for connector in gw_configuration['connectors']:
                connector_conf=None
                mtime=None
                try:
                    with open(self.__gateway.get_config_path() + connector['configuration'], 'r', encoding="UTF-8") as conf_file:
                        connector_conf = load(conf_file)
                        connector_conf["name"] = connector["name"]
                    mtime = stat(self.__gateway.get_config_path() + connector['configuration']).st_mtime
                except Exception as e:
                    LOG.error("Error on loading connector:")
                    LOG.exception(e)
                connectors_configs[connector["name"]]={
                            "type": connector["type"], 
                            "class": connector.get("class"),
                            "mtime": mtime, 
                            "configuration": connector['configuration'], 
                            "config": connector_conf}
            return connectors_configs
        else:
            LOG.error("Connectors - not found! Check your configuration!")

    def __del_connector(self, config_type, config_name):
        try:
            if config_type in self.__gateway.connectors_configs:
                for i in range(len(self.__gateway.connectors_configs[config_type])):
                    if config_name == self.__gateway.connectors_configs[config_type][i]["name"]:
                        del self.__gateway.connectors_configs[config_type][i]
            if config_type in self.__gateway._implemented_connectors:
                del self.__gateway._implemented_connectors[config_type]
            if config_name in self.__gateway.available_connectors:
                connector = self.__gateway.available_connectors[config_name]
                if connector:
                    try:
                        connector.close()
                    except Exception as e:
                        LOG.exception(e)
        except Exception as e:
            LOG.exception(e)

    def __add_connector(self, config, config_type, config_name):
        try:
            connector_class = TBUtility.check_and_import(config_type, 
                self.__gateway._default_connectors.get(config_type, config["class"]))
            self.__gateway._implemented_connectors[config_type] = connector_class
            if config_type not in self.__gateway.connectors_configs:
                self.__gateway.connectors_configs[config_type]=[]
            self.__gateway.connectors_configs[config_type].append({"name": config_name, 
                "config": {config["configuration"]: deepcopy(config["config"])}})

            connector = connector_class(self.__gateway, config["config"], config_type)
            connector.setName(config_name)
            self.__gateway.available_connectors[connector.get_name()] = connector
            try:
                connector.open()
            except Exception as e:
                LOG.exception(e)
        except Exception as e:
            LOG.exception(e)
