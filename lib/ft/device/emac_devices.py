#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

# standard libs
import copy
import datetime 
import serial
from os import path
import os
import subprocess
import sys
import time
import inspect

import logging

from interfaces.xmlrpc import (
        ServerInterface,
        xmlrpc_all,
        )

@xmlrpc_all
class BinaryCall(ServerInterface,):
    def __init__(self, kwargs):
        self.bincmd         = kwargs["binary_full_path"]
        instance_name       = kwargs["instance_name"]

        kwargs_copy = copy.copy(kwargs)

        if kwargs.has_key("xmlrpc_client"):
            xmlrpc_client       = kwargs_copy.pop("xmlrpc_client")
        else:
            xmlrpc_client       = None

        ServerInterface.__init__(self, instance_name, xmlrpc_client, kwargs_copy)

        self.process        = None

    ##
    # @brief call the test binary with the arguments passed from the "test"
    # method. Return exit_status, std_out, and std_err messages.
    def call(self, kwargs):
        args   = [self.bincmd] + kwargs["argslist"]

        logging.debug("About to call binary: {0}".format(args))

        if kwargs.has_key("wait"):
            wait    = kwargs["wait"]
        else:
            wait    = True

        p       = self.process
        if not p == None:
            p.terminate()
            time.sleep(.1)

        if wait:
            p       = subprocess.Popen(args, stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,)

            output  = p.communicate()
            status  = p.returncode

            logging.debug("Binary returned ({0}, {1})".format(status, output))

            p       = None

            return status, output[0]
        else:
            p       = subprocess.Popen(args,) 
            return False, ""

@xmlrpc_all
class Audio(ServerInterface):
    valid_modes = [
            "inout",
            "out",
            ]

    def __init__(self, kwargs):
        instance_name       = kwargs["instance_name"]
        mode                = kwargs["mode"]

        if kwargs.has_key("xmlrpc_client"):
            xmlrpc_client       = kwargs.pop("xmlrpc_client")
        else:
            xmlrpc_client       = None

        ServerInterface.__init__(self, instance_name, xmlrpc_client, kwargs)

        if mode in self.valid_modes:
            self.mode   = mode
        else:
            raise ValueError("Unsupported Audio interface mode.")

    def run(self, kwargs):
        if kwargs.has_key("aplay"):
            aplay_args = [kwargs["aplay"]]

        if kwargs.has_key("arecord"):
            arecord_args = [kwargs["arecord"]]

        arecord_args.extend(kwargs["arecord_args"])

        self.ar  = subprocess.Popen(arecord_args, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)

        self.ap  = subprocess.Popen(aplay_args, stdin=self.ar.stdout,
                stderr=subprocess.PIPE)

        return None, ("", "")

    def stop(self, kwargs):
        self.ar.kill()
        self.ap.kill()

        return None, ("", "")


from fcntl import ioctl

RTDM_CLASS_GPIO = 128

DDRREAD 	    = 2147581952
DDRWRITE 	    = 1073840128

DATAREAD 	    = 2147581953
DATAWRITE 	    = 1073840129

INDEXREAD 	    = 2147581954
INDEXWRITE 	    = 1073840130

DDRREAD_NL 	    = 2147581955
DDRWRITE_NL 	= 1073840131

DATAREAD_NL 	= 2147581956
DATAWRITE_NL 	= 1073840132

INDEXREAD_NL 	= 2147581957
INDEXWRITE_NL 	= 1073840133

GPIOLOCK 	    = 32774
GPIOUNLOCK 	    = 32775

@xmlrpc_all
class GPIO(ServerInterface,):
    def __init__(self, kwargs):
        self.gpio_dir   = kwargs["gpio_dir"]
        
        self.index      = None
        self.data       = None

        if kwargs.has_key("xmlrpc_client"):
            xmlrpc_client       = kwargs.pop("xmlrpc_client")
        else:
            xmlrpc_client       = None

        instance_name = kwargs["instance_name"]

        ServerInterface.__init__(self, instance_name, xmlrpc_client, kwargs)

    def set_device(self, kwargs={},):
        try:
            gpio_dir    = kwargs["gpio_dir"]
            self.__set_device(gpio_dir)

        except Exception as e:
            message = e.args
            result  = "UNKNOWN"
            
        return result, message

    def set_hex(self, kwargs={}): 
        output  = []

        if kwargs.has_key("gpio_dir"):
            gpio_dir = kwargs.pop("gpio_dir")
        else:
            gpio_dir = None

        value   = kwargs["value"]

        try:
            if gpio_dir != None:
                self.__set_device(gpio_dir)
            logging.debug(value)
            self.__write_data("0x" + value)
            self.data   = self.__read_data()
            logging.debug(self.data)
        except Exception as e:
            message = e.args
            result  = "UNKNOWN"
            logging.debug(message)
            raise
        else:
            message = "GPIO Value: {0}".format(self.data)
            result  = "SUCCESS"
            
        return result, message

    def get_hex(self, kwargs={}): 
        output  = []

        if kwargs.has_key("gpio_dir"):
            gpio_dir = kwargs.pop("gpio_dir")
        else:
            gpio_dir = None

        try:
            if gpio_dir != None:
                self.__set_device(gpio_dir)
            self.data  = self.__read_data()
            logging.debug(self.data)
        except Exception as e:
            message = e.args
            result  = "UNKNOWN"
            logging.debug(message)
            raise
        else:
            message = "GPIO Value: {0}".format(self.data)
            result  = "SUCCESS"
            
        return self.data, message

    def get_index(self, kwargs,):
        output  = []
        index   = kwargs["index"]

        try:
            if gpio_dir != None:
                self.__gpio_dir(gpio_dir)
            self.__write_index(index)
            self.value  = self.__read()
        except Exception as e:
            message = e.args
            result  = "UNKNOWN"
        else:
            message = "GPIO Value: {0}".format(self.value)
            result  = "SUCCESS"
            
        return result, message

    def __set_device(self, gpio_dir):
        if not path.exists(gpio_dir):
            raise StandardError("Could not find {0}: no such file or directory"
                    .format(gpio_dir))

        self.gpio_dir    = gpio_dir

    def __read_index(self,):
        gpio_dir    = self.gpio_dir
        with open(path.join(gpio_dir, "index"), "r") as f:
            value   = f.read()[:-2]

        return value

    def __write_index(self, value):
        gpio_dir    = self.gpio_dir
        with open(path.join(gpio_dir, "index"), "w") as f:
            value   = f.write(value)
            
    def __read_data(self,):
        gpio_dir    = self.gpio_dir
        with open(path.join(gpio_dir, "data"), "r") as f:
            value   = f.read()[:-2]

        return value

    def __write_data(self, value):
        gpio_dir    = self.gpio_dir
        with open(path.join(gpio_dir, "data"), "w") as f:
            value   = f.write(value)

## Compact rewrite of the above GPIO interface.
class SysFSInterface(object,):
    def __init__(self, sysfs_dir):
        self.sysfs_dir  = sysfs_dir

    def _read(self, attrname):
        sysfs_dir    = self.sysfs_dir
        with open(path.join(sysfs_dir, attrname), "r") as f:
            value   = f.read()
            setattr(self, attrname, value)

    def _write(self, attrname, value):
        sysfs_dir   = self.sysfs_dir 
        with open(path.join(sysfs_dir, attrname), "w") as f:
            value   = f.write(value)
            self._read(attrname)

@xmlrpc_all
class IndexedAtoD(ServerInterface, SysFSInterface):
    def __init__(self, kwargs):
        sysfs_dir       = kwargs["sysfs_dir"]
        instance_name   = kwargs["instance_name"]

        if kwargs.has_key("xmlrpc_client"):
            xmlrpc_client       = kwargs.pop("xmlrpc_client")
        else:
            xmlrpc_client       = None

        self.data   = None
        self.index  = None

        SysFSInterface.__init__(self, sysfs_dir)

        ServerInterface.__init__(self, instance_name, xmlrpc_client, kwargs)

    def get_analog(self, kwargs):
        nothing, message    = self._get_hex(kwargs)

        float_min, float_max = kwargs["float_range"]
        float_range = float_max - float_min

        float_value = ( (float(int(self.data, 16))/float(int("3ff", 16)))
                * float_range ) - float_min

        return float_value, message

    def get_hex(self, kwargs):
        return self._get_hex(kwargs)

    def _get_hex(self, kwargs):
        if kwargs.has_key("sysfs_dir"):
            sysfs_dir = kwargs.pop("sysfs_dir")
        else:
            sysfs_dir = None

        try:
            # TODO: need to fix the IndexedAtoD driver so that it correctly
            # outputs the current value whenever it is read, rather than always
            # outputing the previous value. For not, the two reads below are
            # necessary to cause the current value to be returned by this
            # function. Once the driver is fixed, this -should- be removed, but
            # does not need to be.
            self._read("data")
            self._read("data")
            logging.debug(self.data)
        except Exception as e:
            message = e.args
            result  = "UNKNOWN"
        else:
            message = "Indexed AtoD Value {0}".format(self.data)
            result  = "SUCCESS"

        logging.debug(self.data)
        return self.data, message

@xmlrpc_all
class PWM(ServerInterface, SysFSInterface):
    def __init__(self, kwargs):
        sysfs_dir       = kwargs["sysfs_dir"]
        instance_name   = kwargs["instance_name"]

        if kwargs.has_key("xmlrpc_client"):
            xmlrpc_client       = kwargs.pop("xmlrpc_client")
        else:
            xmlrpc_client       = None

        self.widthus    = None
        self.periodus   = None

        SysFSInterface.__init__(self, sysfs_dir)

        ServerInterface.__init__(self, instance_name, xmlrpc_client, kwargs)

    def get_periodus(self, kwargs):
        if kwargs.has_key("sysfs_dir"):
            sysfs_dir = kwargs.pop("sysfs_dir")
        else:
            sysfs_dir = None

        try:
            self.periodus   = self._read("periodus")
        except Exception as e:
            message = e.args
            result  = "UNKNOWN"
        else:
            message = "PWM Periodus Value: {0}".format(self.periodus)
            result  = "SUCCESS"

        return result, message

    def set_periodus(self, kwargs):
        value   = kwargs["value"]

        if kwargs.has_key("sysfs_dir"):
            sysfs_dir = kwargs.pop("sysfs_dir")
        else:
            sysfs_dir = None

        try:
            self._write("periodus", "0x" + value)
        except Exception as e:
            message = e.args
            result  = "UNKNOWN"
        else:
            message = "PWM Periodus Value: {0}".format(self.periodus)
            result  = "SUCCESS"

        return result, message

    def get_widthus(self, kwargs):
        if kwargs.has_key("sysfs_dir"):
            sysfs_dir = kwargs.pop("sysfs_dir")
        else:
            sysfs_dir = None

        try:
            self.widthus   = self._read("widthus", "0x")
        except Exception as e:
            message = e.args
            result  = "UNKNOWN"
            raise
        else:
            message = "PWM Widthus Value: {0}".format(self.widthus)
            result  = "SUCCESS"

        return result, message

    def set_widthus(self, kwargs):
        value   = kwargs["value"]

        if kwargs.has_key("sysfs_dir"):
            sysfs_dir = kwargs.pop("sysfs_dir")
        else:
            sysfs_dir = None

        try:
            self._write("widthus", "0x" + value)
        except Exception as e:
            message = e.args
            result  = "UNKNOWN"
        else:
            message = "PWM Widthus Value: {0}".format(self.widthus)
            result  = "SUCCESS"

        return result, message

@xmlrpc_all
class RS485(ServerInterface):
    def __init__(self, devices):
        raise NotImplementedError

@xmlrpc_all
class EMACSerial(ServerInterface,):
    def __init__(self, kwargs):

        if kwargs.has_key("xmlrpc_client"):
            xmlrpc_client       = kwargs.pop("xmlrpc_client")
        else:
            xmlrpc_client       = None

        instance_name = kwargs["instance_name"]

        ServerInterface.__init__(self, instance_name, xmlrpc_client, kwargs)
        
        baud    = kwargs["baud"]
        dev     = kwargs["dev"]

        if self._is_local():
            self.serial = serial.Serial(dev, baud)
            self.buf    = None
        else:
            self.serial = None
            self.buf    = None

    def read(self, kwargs,):
        tmp                 = self.serial.timeout
        self.serial.timeout = 1

        size                = kwargs["size"]

        buf                 = self.serial.read(size)
        buf = buf.translate(None, "\x00")
        self.serial.timeout = tmp
        return buf, None

    def write(self, kwargs):
        data    = kwargs["data"]
        self.serial.write(data)

    def _run(self,):

        for device in self.devices:

            try:
                s       = serial.Serial(device["file_name"], writeTimeout=5, timeout=5) 
                if device["options"] != "":
                    p   = serial.Serial(device["options"], writeTimeout=5, timeout=5)
                else:
                    p   = s

                test_string = "Test String!!"
                s.write(test_string + "\n")
                veri_string = p.readline()

            except (SerialException, SerialWriteException) as e:
                self.__fail(device["file_name"], e.strerr)
                return False

            if not veri_string == test_string:
                self.__fail(device["file_name"], "Incorrect string read back.")
                return False
            
        return True

@xmlrpc_all
class Block(ServerInterface):
    def __init__(self, devices):
        ServerInterface.__init__(self,)
        #raise NotImplementedError()

    def _run(self,):
        return "your mom"

    def mount(self,):
        raise NotImplementedError

    def read(self,):
        raise NotImplementedError

    def write(self,):
        raise NotImplementedError

if __name__ == "__main__":
    if sys.argv[1]  == "1":
        # control machine
        sys.path.append(path.abspath("emactest/interfaces/"))
        sys.path.append(path.abspath("emactest/"))

        from adam.adam_module_examples import *
        from adam.lib.interface import ADAMInterface

        adam        = ADAMInterface(baud=9600, serial_dev="/dev/ttyS3")
        #adam4017p   = ADAM_4017P(adam, "01")
        adam4024    = ADAM_4024(adam, "06")
        adam4050    = ADAM_4050(adam, "04")
        adam4051    = ADAM_4051(adam, "03")
        adam4068    = ADAM_4068(adam, "02")
        logging.debug("ADAM Initialization Successful")

        gpio_kwargs = {
                "gpio_dir"   : "/sys/class/gpio/ocout",
                "instance_name" : "OpenCollectorOut",
                }
        g   = GPIO(gpio_kwargs)
        g.read(kwargs={})

    elif sys.argv[1] == "2":
        # uut
        gpio_kwargs = {
                "gpio_dir"   : "/sys/class/gpio/ocout",
                "instance_name" : "OpenCollectorOut",
                }

        g   = GPIO(gpio_kwargs)

        inp = "f"
        while inp != "quit":
            kwargs  = {
                    "value" : "0x" + inp,
                    }

            g.write(kwargs)
            g.read(kwargs={})

            inp = raw_input(" ")


