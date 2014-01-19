#!/usr/bin/env python

from datetime import datetime
import sys, logging

from util.locker import (
        locker_all
        )

@locker_all
class SerialInterface(object):

    def __init__(self, enhanced_serial=None, debug=True):
        self.dbg = debug

        self.serial = enhanced_serial

        self.buf        = []
        self.buf_new    = []

    def setup(self):
        self.serial.setup()

    def release(self):
        self.serial.release()

    ## Use this serial interface to run a command on the remote board.
    #
    # @param command This is a command which should be compliant with the remote
    # board's command line. 
    # @param prompt This is the "prompt" which the remote machine outputs to
    # indicate it is ready to receive a command. This can vary from bootloader
    # to bootloader or from one product type to another.
    # @param timeout This is the amount of time that the function should wait to
    # see the next prompt; if the timeout is exceeded, then return False to
    # indicate lack of success.
    #
    def cmd(self, 
            command     = "printenv", 
            prompt      = None,
            timeout     = 50):

        if prompt == None:
            prompt  = self.prompt

        serial  = self.serial

        test, self.buf_new = serial.read_until(
                prompt,
                command = command + '\n',
                timeout = timeout
                )

        if test:
            logging.debug("Command Succeeded: {0}".format(command))
            return True, self.buf_new

        logging.debug("Command Failed: {0}".format(command))

        return False, self.buf_new

    def abort(self,
            prompt  = None,
            timeout = 1):
        if prompt == None:
            prompt  = self.prompt
        serial = self.serial

        # check that the prompt is ready
        test, self.buf_new = serial.read_until(
                prompt,
                command = "\x03",
                debug = 0,
                timeout = timeout
                )

        if test:
            return True

        logging.warning("Abort failed, no prompt found afterward.")
        return False

class SerialInterfaceError(Exception):

    def __init__(self, message):
        self.message = ("Serial Interface error: {0}").format(message)
    
    def __str__(self):
        return repr(self.message)

