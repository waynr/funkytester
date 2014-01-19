#!/usr/bin/env python

# standard modules
import time, copy, sys, logging
from decimal import Decimal

# distro modules

baud_table = {
        1200    : "03",
        2400    : "04",
        4800    : "05",
        9600    : "06",
        19200   : "07",
        38400   : "08",
        57600   : "09",
        115200  : "0A",
        }

class ADAMModule(object):

    def __init__(self, adam_interface, address="00", debug=True ):
        self.address    = address
        self.interface  = adam_interface
        self.debug      = debug

        self.name       = self.module_name()

    def is_valid(self, module_list):
        name    = self.name

        if not name in module_list:
            raise TypeError("{0} cannot be used with {0}".
                    format(name, self.__class__.__name__))

    def module_info(self):
        adam_interface  = self.interface

        for info_function in [
                self.module_name, 
                self.firmware_version,
                self.config_status, ]:
            result = info_function()
            print(result)

    def _set(self, command, cut_address=False):
        adam_interface  = self.interface

        # run query
        adam_interface.cmd(
                delimiter   = "#",
                address     = self.address,
                options     = command,
                )

        # TODO error-check response
        return adam_interface.response(cut_address)

    def query(self, command, cut_address=False):
        # TODO error-check command
        #  * check against a list of possible valid commands?
        #  * verify alphanumeric characters are used

        command = command.upper()

        adam_interface  = self.interface

        # run query
        adam_interface.cmd(
                delimiter   = "$",
                address     = self.address,
                options     = command,
                )

        return adam_interface.response(cut_address)

    def firmware_version(self):
        return self.query("F", True)[0]

    def module_name(self):
        return self.query("M", True)[0]

    def config_status(self):
        return self.query("2", True)[0]

    def config(self, **kwargs):
        adam_interface  = self.interface

        if kwargs.has_key("baud_rate"):
            baud    = kwargs["baud_rate"]
            baud    = baud_table[baud]
        else:
            baud    = "06" # 9600

        new         = kwargs["new"]

        # TODO factor type_code and extra into class values
        type_code   = kwargs["type_code"]
        extra       = kwargs["extra"]

        adam_interface.cmd(
                delimiter   = "%",
                address     = self.address,
                options     = new + type_code + baud + extra,
                )

        return adam_interface.response(True)

def convert_float2data(float_value):
    t           = type(float_value)
    valid_types = [
            type(int()),
            type(float()),
            ]

    maxb    = 99.999
    minb    = -99.999

    if t not in valid_types:
        raise TypeError("Input must be a Real number (received: {0})."
                .format(float_value)
                )


    if float_value < minb or float_value > maxb:
        raise ValueError("Input value must be between {0} and {1}."
                .format(minb, maxb)
                )

    return "{0:+07.3f}".format(float_value)

class ADAMAnalogModule(ADAMModule):

    def __init__(self, adam_interface, address="00", units="engr"):
        ADAMModule.__init__(self, adam_interface, address)
        
        self.units      = units

        if self.__dict__.has_key("channels"):
            self.channels["analog_inputs"] = list()
            self.channels["analog_outputs"] = list()
        else:
            self.channels   = {
                    "analog_inputs"  : list(),
                    "analog_outputs" : list(),
                    }

    def get_analog(self,):
        self._get_analog()
        return copy.deepcopy(self.channels)

    def _get_analog(self,):
        ao      = self.channels["analog_outputs"]
        ai      = self.channels["analog_inputs"]

        ai_len  = len(ai)
        ao_len  = len(ao)

        if ao_len > 0:
            for i in range(0, ao_len):
                # We take the last value sent rather than the current readback
                # value because the documentation does not specify what exactly
                # is supposed to be returned by the current readback.
                response    = self.query("6C{0}".format(i), cut_address=True)
                ao[i]       = float(response[0])

        if ai_len > 0:
            for i in range(0, ai_len):
                # We take the last value sent rather than the current readback
                # value because the documentation does not specify what exactly
                # is supposed to be returned by the current readback.
                response    = self._set("{0}".format(i), cut_address=True)
                ai[i]       = float(response[0])


INP_RANGE_CODE1 = {
        "10V"   : "08",
        "5V"    : "09",
        "1V"    : "0A",
        "500mV" : "0B",
        "150mV" : "0C",
        "50mV"  : "0D",
        }
INP_RANGE_CODES = {
        "4012"  : INP_RANGE_CODE1,
        "4017"  : INP_RANGE_CODE1,
        "4017P" : INP_RANGE_CODE1,
        }

class ADAMAnalogInModule(ADAMAnalogModule):

    ai_modules = [ 
            "4017P",
            ]

    def __init__(self, adam_interface, address="00", analog_ins=8, 
            input_range="10V"):
        ADAMAnalogModule.__init__(self, adam_interface, address)

        self.is_valid(self.ai_modules)
        name    = self.name

        if not input_range in INP_RANGE_CODES[name].keys():
            raise ValueError("{0} is not a valid input range."
                    .format(input_range)
                    )

        input_type_code = INP_RANGE_CODES[name][input_range]

        self.config(
                baud_rate   = 9600,
                new         = self.address,
                type_code   = input_type_code,
                extra       = "00",
                )

        for channel in range(0, analog_ins):
            self.channels["analog_inputs"].append(float())
            #self.query("7C{0}R{1}".format(channel, input_type_code))

class ADAMAnalogOutModule(ADAMAnalogModule):

    ao_modules = [ 
            "4024",
            ]

    def __init__(self, adam_interface, address="00", analog_outs=4, 
            slew_rate="00", output_type="32"):
        ADAMAnalogModule.__init__(self, adam_interface, address)

        self.is_valid(self.ao_modules)

        sr  = int(slew_rate, 16)
        sr  = "{0:04b}".format(sr)

        extra   = "01" + sr + "00"
        extra   = int(extra, 2)
        extra   = "{0:02X}".format(extra)

        self.config(
                baud_rate   = 9600,
                new         = self.address,
                type_code   = "00",
                extra       = extra,
                )
        
        for channel in range(0, analog_outs):
            self.channels["analog_outputs"].append(float())
            # set this channel to +/- 10 V digital output
            self.query("7C{0}R{1}".format(channel, output_type))

    def set_analog(self, channel_list, float_value):
        for channel in channel_list:
            self._set_analog(channel, float_value)

    def _set_analog(self, channel, float_value):
        data    = convert_float2data(float_value)

        minb    = 0
        maxb    = len(self.channels["analog_outputs"])

        if channel < minb or channel > maxb:
            raise ValueError("The channel specification for this instance must \
be between {0} and {1}".format(minb, maxb))

        data    = convert_float2data(float_value)
        command ="C{0}{1}".format(channel, data)
        self._set(command)

def convert_dig2int(digital):
    # given a list of digital integer values, convert them to their hexadecimal
    # text representation
    if not type(digital) == type(list()):
        raise TypeError("Expected {0}, got {1}."
                .format(
                    type(list()),
                    type(digital)
                    )
                )
    digital.reverse()
    
    result  = 0
    for i, bit in enumerate(digital):
        result  = result + bit * ( 2 ** i )

    return result

def convert_int2hexstr(i):
    maxb    = int("FFFF", 16)
    minb    = int("0000", 16)
    if i > maxb or i < minb:
        raise ValueError("Expected integer between {0} and {1}, got {0}"
                .format(minb, maxb, i))

    return "{0:02X}".format(i)

def convert_dig2hexstr(digital):
    return convert_int2hexstr(convert_dig2int(digital))

class ADAMDigitalModule(ADAMModule):

    d_modules = [ 
            "4050",
            "4051",
            "4068",
            "4024",
            ]

    def __init__(self, adam_interface, address="00",):
        ADAMModule.__init__(self, adam_interface, address)

        self.is_valid(self.d_modules)

        if not self.__dict__.has_key("hexvals"):
            self.hexvals   = {
                    "inputs"  : list(),
                    "outputs" : list(),
                    }

        if not self.__dict__.has_key("channels"):
            self.channels   = {
                    "inputs"  : list(),
                    "outputs" : list(),
                    }

    def _invert_hexval(self, channel):
        channel_len = len(self.channels[channel])
        mask        = int("{0:s}".format("1" * channel_len), 2)

        hexval                  = self.hexvals[channel]
        hexval                  = int(hexval, 16)
        hexval                  = (mask & hexval) ^ mask
        self.hexvals[channel]   = "{0:02x}".format(hexval)

    def get_hex(self, t="both", invert_input=False):
        if self._get_hex():
            if invert_input:
                self._invert_hexval("inputs")

            if t == "inputs":
                return copy.deepcopy(self.hexvals["inputs"])
            elif t == "outputs":
                return copy.deepcopy(self.hexvals["outputs"])
            else:
                return copy.deepcopy(self.hexvals)
        else:
            raise ValueError("No digital inputs or outputs acquired.")

    def _get_hex(self,): 
        di          = self.channels["inputs"]
        do          = self.channels["outputs"]

        di_len      = len(di)
        do_len      = len(do)

        try:
            if self.name == "4024":
                response    = self.query("I", cut_address=True)
            else:
                response    = self.query("6")
        except Exception as e :
            message = e.args
            result  = "UNKOWN"
            logging.debug(message)
            raise 

        inputs  = ""
        outputs = ""

        if do_len > 0:
            outputs = response[0][0:2]
            self.hexvals["outputs"]  = outputs

            if di_len > 0:
                inputs  = response[0][2:4]
                self.hexvals["inputs"]  = inputs
            return True

        elif di_len > 0:
            inputs  = response[0][0:di_len/4]
            self.hexvals["inputs"]  = inputs
            return True

    def get_digital(self, t="both", selection=None):
        if self._get_digital():
            if t == "inputs":
                output  = copy.deepcopy(self.channels["inputs"])
            elif t == "outputs":
                output  = copy.deepcopy(self.channels["outputs"])
            else:
                output  = copy.deepcopy(self.channels)
            return self._filter(output, selection)

        else:
            raise ValueError("No digital inputs or outputs acquired.")

    def _filter(self, digital, selection=None):
        if selection == None:
            return digital

        else:
            d_len   = len(digital)
            # MSB is always considered to be on the left since that makes sense
            # to me (and it is too late to change now anyway)...there are better
            # ways than using "reverse()" but I don't feel like troubleshooting
            # my poor mental arithmetic right now. 
            digital.reverse()
            for i in range(d_len):
                if not i in selection:
                    digital[i]  = "x"
            digital.reverse()

        return digital

    def _get_digital(self,):
        self._get_hex()

        di_len      = len(self.channels["inputs"])

        if di_len > 0:
            inputs      = int(self.hexvals["inputs"], 16)

            di_binary  = "{0:0{length}b}".format(inputs, length=di_len)
            for i in range(di_len):
                self.channels["inputs"][i]  = int(di_binary[i])

        do_len      = len(self.channels["outputs"])
        if do_len > 0:
            outputs     = int(self.hexvals["outputs"], 16)

            do_binary  = "{0:0{length}b}".format(outputs, length=do_len)
            for i in range(do_len):
                self.channels["outputs"][i]  = int(do_binary[i])

        return True

    def _get_digital_old(self,):
        di          = self.channels["inputs"]
        do          = self.channels["outputs"]

        di_len      = len(di)
        do_len      = len(do)

        if self.name == "4024":
            response    = self.query("I", cut_address=True)
        else:
            response    = self.query("6")

        if do_len > 0:
            outputs = response[0][0:2]
            h       = int(outputs, 16)
            binary  = "{0:0{length}b}".format(h, length=do_len)
            logging.debug(binary)
            outputs = list(binary)
            for i, bit in enumerate(outputs):
                self.channels["outputs"][i]    = int(bit)

            if di_len > 0:
                inputs  = response[0][2:4]
                h       = int(inputs, 16)
                binary  = "{0:0{length}b}".format(h, length=di_len)
                inputs  = list(binary)
                for i in range(di_len):
                    print(inputs)
                    self.channels["inputs"][i]    = int(inputs[i])

            return True

        if di_len > 0:
            inputs  = response[0][0:di_len/4]
            h       = int(inputs, 16)
            binary  = "{0:0{length}}".format(h, length=di_len)
            for i, bit in enumerate(inputs):
                print(inputs)
                self.channels["inputs"][i]    = int(bit)

            return True

        return False

    def _create_mask(self, channel_list):
        mask = 0

        for channel in channel_list:
            if not channel in self.DO.keys():
                print("Must specify a valid list of channels!")
            mask &= 1 << channel            

        return str(hex(mask))

class ADAMDigitalInModule(ADAMDigitalModule):

    valid_modules = [ 
            "4050",
            "4051",
            ]

    def __init__(self, adam_interface, address="00", digital_ins=8):
        ADAMDigitalModule.__init__(self, adam_interface, address)

        for i in range(0, digital_ins):
            self.channels["inputs"].append(0)

        self._get_digital()

class ADAMDigitalOutModule(ADAMDigitalModule):

    do_modules = [ 
            "4050",
            "4068",
            ]

    def __init__(self, adam_interface, address="00", digital_outs=8):
        ADAMDigitalModule.__init__(self, adam_interface, address)

        for i in range(0, digital_outs):
            self.channels["outputs"].append(0)

        self._get_digital()

    def set_hex(self, hexstr, invert_output=False):
        bb              = "00"
        data1           = ""

        self.hexvals["outputs"] = hexstr
        if invert_output:
            self._invert_hexval("outputs")
            
        data2   = self.hexvals["outputs"]

        logging.debug(bb + data1 + data2)
        response        = self._set(bb + data1 + data2)

        return True

    def set_mask(self, mask, value):
        self._get_digital()
        do  = self.channels["outputs"]

        intmask     = int(mask, 16)
        original    = convert_dig2int(do)

        if value == 0:
            intmask = ~intmask & original
        elif value == 1:
            intmask = intmask | original
        else:
            raise ValueError("Digital value must be either 0 or 1, got {0}."
                    .format(value))

        new_value   = convert_int2hexstr(intmask)

        self.set_hex(new_value)

        return True

    def set_digital(self, channels, value):
        self._get_digital()
        do  = self.channels["outputs"]

        if value > 1 or value < 0:
            raise ValueError("Value must be high (1) or low (0)")

        minb    = 0
        maxb    = len(do) - 1

        for i in channels:
            if i < minb or i > maxb:
                raise IndexError("Channel values must be between {0} and {1}"
                        .format(minb, maxb))
            do[maxb - i] = value

        new_value   = convert_dig2hexstr(do)
        self.set_hex(new_value)

        return True


if __name__ == "__main__":
    # local modules
    from interface import ADAMInterface

    adam = ADAMInterface(serial_dev = "/dev/ttyS3", baud = 9600)
    modules = [ '04', '02', '06', ]

    for i, address in enumerate(modules):
        modules[i]  = ADAMModule(adam, address)

    for m in modules:
        m.module_info()
        print("")

    adam.cli()

