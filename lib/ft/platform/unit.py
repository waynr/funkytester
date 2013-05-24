#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

## @package unit
#
#  Provides abstractions necessary to represent a whole "Unit Under Test" using
#  various interfaces.
#

import logging, threading

import fysom

from sqlalchemy import ( Column, Integer, String, Boolean, DateTime, Text,
        ForeignKey )
from sqlalchemy.orm import relationship

from interfaces import (
        xmlrpc,
        ADAMInterface, 
        ADAM_4068, 
        UBootTerminalInterface, 
        LinuxTerminalInterface,
        adam,
        )

import ft.event
from ft import Base
from ft.command import Commandable
from ft.test import Test

## Representation of a UUT for logging/viewing purposes.
#
#  Represent the UUT during test log view. In this case, only the ORM aspects of
#  the UUT are pertinent so the base UnitUnderTest class is unmodified after
#  declaring those attributes.
#
class UnitUnderTestDB(Base):

    __tablename__ = "pyft_unit_under_test"
    id = Column(Integer, primary_key=True)
    serial_num = Column(String(20))
    datetime_tested = Column(DateTime)
    fail = Column(Boolean)
    comment = Column(Text)
    status = Column(String(20))

    platform_slots = Column(Integer, ForeignKey('pyft_platform_slot.id'))
    product = Column(Integer, ForeignKey('pyft_product.id'))
    technician = Column(Integer, ForeignKey('pyft_user.id'))

    tests = relationship("Test")

    class Status:
        INIT = "Initialized"
        BUSY = "Busy"

    def __repr__(self,):
        rstring = "<UnitUnderTest('%s','%s','%s')>" 
        rtuple = self.name, self.serialnum, self.status
        return rstring % rtuple

## Representation of a UUT for testing purposes.
#
#  Provide the methods and attributes necessary to control the unit being tested
#  from powerdown to command line prompt back to powerdown again. This includes
#  encapsulating unit "state" using fysom. This mode should only be available if
#  the UUT object has been assigned at minimum a serial port on which it can
#  listen for messages from the actual UUT.
#  
class UnitUnderTest(UnitUnderTestDB, Commandable):

    def __init__(self, config, parent=None, serial_number="0000000000"):
        self.serial_num = serial_number
        self.product = None
        self.macaddr = None
        self.ip_address = None
        self.status = self.Status.INIT

        self.com = config["control"]["com"]
        self.adam = config["control"]["adam"]

        self.parent = parent

        self.lock = threading.RLock()

    def set_address(self, address):
        self.address = (self.parent.address, address)
        self.fire( ft.event.UUTInit,
                obj = self,
                name = self.serial_num,
                status = self.status,
                )

    def fire(self, event, **kwargs):
        self.parent.fire(event, **kwargs)

    def configure(self, serial_num, product, macaddr=None):
        self.serial_num = serial_num
        self.product = product
        self.macaddr = macaddr

        self.serial = self.parent.get_serialport()
        self.interfaces = { 
                "linux" : LinuxTerminalInterface(
                    prompt = self.product.config.prompt["linux"]["standard"],
                    enhanced_serial = self.serial,
                    ),
                "uboot" : UBootTerminalInterface(
                    prompt = self.product.config.prompt["uboot"],
                    enhanced_serial = self.serial,
                    )
                }

        self.__init_adam()

        self.specification = self.product.specification

        self.fire( ft.event.UUTReady,
                obj = self,
                name = self.serial_num,
                status = self.status,
                )

    def __load_testlist(self):
        self.testlist = list()

        for test_dict in self.specification["testlist"]:
            newtest = Test(test_dict, self, None)
            self.testlist.append(newtest)

    def __init_adam(self):

        # --------------------
        # Check Available Tools
        # 
        adam_4068_address = self.adam["address"]
        adam_4068_available = True
        try:
            adam_interface = adam.get_adam_interface()
            adam_4068 = ADAM_4068(adam_interface, adam_4068_address)
            logging.info("ADAM Modules detected")
        except NameError:
            adam_4068_available = False
            raise
         
        # --------------------
        # Set up state
        # 
        boot_pin = self.adam["pins"]["boot"]
        pwr_pin = self.adam["pins"]["power"]

        self.state = UUTState()
        self.bootpin = BootPin(adam_4068, boot_pin)
        self.power = PowerPin(adam_4068, pwr_pin)
        self.backlight = PowerPin(adam_4068, 0)

    ## Check UUT's current operational state.
    #
    def query(self,):
        pass
    
    class CommandsSync:
        @staticmethod
        def acknowledge(uut, data):
            return data, ""

    class CommandsAsync:
        @staticmethod
        def acknowledge(uut, data):
            pass

## Default action on statechange.
#
def onchangestate(e):
    logging.debug("\'{0}\': \'{1}\' to \'{2}\'.".format( e.event, e.src, 
        e.dst ))

class PowerPin(fysom.Fysom,):

    def __init__(self, adam_4068, relay_pin):
        self.relay = adam_4068
        self.relay_pin_list = [relay_pin]
    
        fysom.Fysom.__init__(self, {
            'initial' : 'off',
            'events' : [

                { 'name' : 'poweroff', 
                    'src' : [ 'on', ],
                    'dst' : 'off' },

                { 'name' : 'poweron', 
                    'src' : 'off', 
                    'dst' : 'on' },

                ],
            'callbacks' : {
                'onchangestate' : onchangestate,
                'onenteron' : self.__power_up,
                'onenteroff' : self.__power_down,
                },
            } )

    def __power_up(self, e):
        self.relay.set_digital(self.relay_pin_list, 1)

    def __power_down(self, e):
        self.relay.set_digital(self.relay_pin_list, 0)

class BootPin(fysom.Fysom,):

    def __init__(self, adam_4068, relay_pin):
        self.relay      = adam_4068
        self.relay_pin_list  = [relay_pin]
    
        fysom.Fysom.__init__(self, {
            'initial' : 'nfe',
            'events' : [

                { 'name' : 'enable', 
                    'src' : [ 'nfd', ],
                    'dst' : 'nfe' },

                { 'name' : 'disable', 
                    'src' : 'nfe', 
                    'dst' : 'nfd' },

                ],
            'callbacks' : {
                'onchangestate' : onchangestate,
                'onenternfd' : self.__disable,
                'onenternfe' : self.__enable,
                },
            } )
     
    def __enable(self, e):
        self.relay.set_digital(self.relay_pin_list, 1)

    def __disable(self, e):
        self.relay.set_digital(self.relay_pin_list, 0)

class UUTState(fysom.Fysom,):

    def __init__(self,):
        fysom.Fysom.__init__(self, {
            'initial' : 'poweroff',
            'events' : [

                { 'name' : 'powerdown', 
                    'src' : [ 'linux', 'uboot', 'null', 'sambam', ],
                    'dst' : 'poweroff' },

                { 'name' : 'pusambam', 
                    'src' : 'poweroff', 
                    'dst' : 'sambam' },

                { 'name' : 'puuboot', 
                    'src' : 'poweroff', 
                    'dst' : 'uboot' },

                { 'name' : 'btlinux', 
                    'src' : 'uboot', 
                    'dst' : 'linux' },

                ],
            'callbacks' : {
                'onchangestate' : onchangestate,
                },
            } )

