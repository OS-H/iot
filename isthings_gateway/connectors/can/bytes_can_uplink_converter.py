
import struct

from connectors.converter import log
from connectors.can.can_converter import CanConverter


class BytesCanUplinkConverter(CanConverter):
    def convert(self, configs, can_data):
        result = {"attributes": {},
                  "telemetry": {}}

        for config in configs:
            try:
                tb_key = config["key"]
                tb_item = "telemetry" if config["is_ts"] else "attributes"

                # The 'value' variable is used in eval
                if config["type"][0] == "b":
                    value = bool(can_data[config["start"]])
                elif config["type"][0] == "i" or config["type"][0] == "l":
                    value = int.from_bytes(can_data[config["start"]:config["start"] + config["length"]],
                                           config["byteorder"],
                                           signed=config["signed"])
                elif config["type"][0] == "f" or config["type"][0] == "d":
                    fmt = ">" + config["type"][0] if config["byteorder"][0] == "b" else "<" + config["type"][0]
                    value = struct.unpack_from(fmt,
                                               bytes(can_data[config["start"]:config["start"] + config["length"]]))[0]
                elif config["type"][0] == "s":
                    value = can_data[config["start"]:config["start"] + config["length"]].decode(config["encoding"])
                else:
                    log.error("Failed to convert CAN data to TB %s '%s': unknown data type '%s'",
                              "time series key" if config["is_ts"] else "attribute", tb_key, config["type"])
                    continue

                if config.get("expression", ""):
                    result[tb_item][tb_key] = eval(config["expression"],
                                                   {"__builtins__": {}} if config["strictEval"] else globals(),
                                                   {"value": value, "can_data": can_data})
                else:
                    result[tb_item][tb_key] = value
            except Exception as e:
                log.error("Failed to convert CAN data to TB %s '%s': %s",
                          "time series key" if config["is_ts"] else "attribute", tb_key, str(e))
                continue
        return result
