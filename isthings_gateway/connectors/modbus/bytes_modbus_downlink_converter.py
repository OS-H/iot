
from pymodbus.payload import BinaryPayloadBuilder
from pymodbus.constants import Endian
from struct import unpack, pack

from connectors.modbus.modbus_converter import ModbusConverter, log


class BytesModbusDownlinkConverter(ModbusConverter):

    def __init__(self, config):
        self.__config = config

    def convert(self, config, data):
        byte_order_str = config.get("byteOrder", "LITTLE")
        byte_order = Endian.Big if byte_order_str.upper() == "BIG" else Endian.Little
        builder = BinaryPayloadBuilder(byteorder=byte_order)
        builder_functions = {"string": builder.add_string,
                             "bits": builder.add_bits,
                             "8int": builder.add_8bit_int,
                             "16int": builder.add_16bit_int,
                             "32int": builder.add_32bit_int,
                             "64int": builder.add_64bit_int,
                             "8uint": builder.add_8bit_uint,
                             "16uint": builder.add_16bit_uint,
                             "32uint": builder.add_32bit_uint,
                             "64uint": builder.add_64bit_uint,
                             "16float": builder.add_16bit_float,
                             "32float": builder.add_32bit_float,
                             "64float": builder.add_64bit_float}
        value = None
        if data.get("data") and data["data"].get("params") is not None:
            value = data["data"]["params"]
        else:
            value = config["value"]
        lower_type = config.get("type", config.get("tag", "error")).lower()
        if lower_type == "error":
            log.error('"type" and "tag" - not found in configuration.')
        variable_size = config.get("objectsCount", config.get("registersCount",  config.get("registerCount", 1))) * 8
        if lower_type in ["integer", "dword", "dword/integer", "word", "int"]:
            lower_type = str(variable_size) + "int"
            assert builder_functions.get(lower_type) is not None
            builder_functions[lower_type](int(value))
        elif lower_type in ["uint", "unsigned", "unsigned integer", "unsigned int"]:
            lower_type = str(variable_size) + "uint"
            assert builder_functions.get(lower_type) is not None
            builder_functions[lower_type](int(value))
        elif lower_type in ["float", "double"]:
            lower_type = str(variable_size) + "float"
            assert builder_functions.get(lower_type) is not None
            builder_functions[lower_type](float(value))
        elif lower_type in ["coil", "bits", "coils", "bit"]:
            assert builder_functions.get("bits") is not None
            if variable_size/8 > 1.0:
                builder_functions["bits"](value)
            else:
                return bytes(bool(int(value)))
        elif lower_type in ["string"]:
            assert builder_functions.get("string") is not None
            builder_functions[lower_type](value)
        elif lower_type in builder_functions and 'int' in lower_type:
            builder_functions[lower_type](int(value))
        elif lower_type in builder_functions and 'float' in lower_type:
            builder_functions[lower_type](float(value))
        elif lower_type in builder_functions:
            builder_functions[lower_type](value)
        else:
            log.error("Unknown variable type")

        builder_converting_functions = {5: builder.to_coils,
                                        15: builder.to_coils,
                                        6: builder.to_registers,
                                        16: builder.to_registers}

        function_code = config["functionCode"]

        if function_code in builder_converting_functions:
            builder = builder_converting_functions[function_code]()
            log.debug(builder)
            if "Exception" in str(builder):
                log.exception(builder)
                builder = str(builder)
            if isinstance(builder, list) and len(builder) not in (8, 16, 32, 64):
                builder = builder[0]
            return builder
        log.warning("Unsupported function code, for the device %s in the Modbus Downlink converter", config["device"])
        return None
