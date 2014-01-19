#!/usr/bin/env python

# standard modules
import sys, re, time, logging

# installed modules
from eserial import OldEnhancedSerial

# local modules
import util

adam_interface = None

def get_adam_interface(dev=None, baud=None, timeout=0.01):
    global adam_interface
    if dev and baud:
        serial = OldEnhancedSerial(port=dev, baudrate=baud, timeout=timeout)
        adam_interface = ADAMInterface(serial)

    if not adam_interface:
        raise ADAMError()
    return adam_interface

class ADAMInterface(object):

    def __init__(self, eserial, debug=True):
        self.dbg = debug

        self.current = {
                "command" : "",
                "response" : "",
                }

        self.serial = eserial

    def debug(self, debug=False):
        self.dbg = debug

    def display_response(self,):
        response    = self.response(False)
        if response != '':
            address, data = response
            logging.debug (address + " " + data)
        else:
            logging.debug ("No response!")

    ## Send a command to the ADAM module
    # @method 
    def cmd(self,**kwargs):
        serial      = self.serial

        delimiter   = kwargs['delimiter']

        if not util.isDelimiter(delimiter):
            logging.debug("'{0}' is not a proper delimiter character. " \
                    "Please use only \ one of the following characters: $%#@"
                    .format(delimiter))
            return None

        address     = kwargs['address']

        if not util.isAddress(address) and not address == "**":
            logging.debug("{0} must be a two-digit hexadecimal value.".format(
                address))
            return None

        options     = kwargs.get('options', "")
        data        = kwargs.get('data', "")

        command = delimiter + address + options + data
        logging.debug(command)
        self.current["command"] = command

        # clear input buffer of junk
        serial.flushInput()

        # send command
        serial.write(command + "\r")

        # read input buffer for response:
        test, data  = serial.read_until("\r")

        # wait a little...

        if not test:
            raise NameError("ADAM Module from address {0} not found."
                    .format(address))

        delimiter   = data[0]
        data        = data[1:-1]

        if delimiter == "?":
            self.current["response"]    = "ERROR"
        else:
            self.current["response"]    = data

        return delimiter, data

    def response(self, cut_address=True):
        # for some reason, not all commands return an address so we have to give
        # modules the option of cutting the address out and moving it to the
        # outside so that we can give a consistent response interface

        data        = self.current["response"]

        # cut out the address, and carriage return
        if cut_address:
            address     = data[0:2]
            start_index = 2
        else:
            address     = ''
            start_index = 0

        data        = data[start_index:]

        # move the address to the last position since it is not always included
        return data, address


