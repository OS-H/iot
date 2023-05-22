
import struct

from connectors.converter import log
from connectors.can.can_converter import CanConverter


class BytesCanDownlinkConverter(CanConverter):
    def convert(self, config, data):
        try:
            if config.get("dataInHex", ""):
                return list(bytearray.fromhex(config["dataInHex"]))

            if not isinstance(data, dict) or not data:
                log.error("Failed to convert TB data to CAN payload: data is empty or not a dictionary")
                return

            if data.get("dataInHex", ""):
                return list(bytearray.fromhex(data["dataInHex"]))

            if config.get("dataExpression", ""):
                value = eval(config["dataExpression"],
                             {"__builtins__": {}} if config.get("strictEval", True) else globals(),
                             data)
            elif "value" in data:
                value = data["value"]
            else:
                log.error("Failed to convert TB data to CAN payload: no `value` or `dataExpression` property")
                return

            can_data = []

            if config.get("dataBefore", ""):
                can_data.extend(bytearray.fromhex(config["dataBefore"]))

            if isinstance(value, bool):
                can_data.extend([int(value)])
            elif isinstance(value, int) or isinstance(value, float):
                byteorder = config["dataByteorder"] if config.get("dataByteorder", "") else "big"
                if isinstance(value, int):
                    can_data.extend(value.to_bytes(config.get("dataLength", 1),
                                                   byteorder,
                                                   signed=(config.get("dataSigned", False) or value < 0)))
                else:
                    can_data.extend(struct.pack(">f" if byteorder[0] == "b" else "<f", value))
            elif isinstance(value, str):
                can_data.extend(value.encode(config["dataEncoding"] if config.get("dataEncoding", "") else "ascii"))

            if config.get("dataAfter", ""):
                can_data.extend(bytearray.fromhex(config["dataAfter"]))

            return can_data
        except Exception as e:
            log.error("Failed to convert TB data to CAN payload: %s", str(e))
            return
