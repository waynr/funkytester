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

    def __init__(self, config, parent=None):
        self.serial_num = "0000000000"
        self.product = None
        self.macaddr = None
        self.ip_address = None
        self.status = self.Status.INIT

        self.com = config["control"]["com"]
        self.adam = config["control"]["adam"]

        self.parent = parent

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

    def _init_adam(self):

        # --------------------
        # Check Available Tools
        # 
        adam_serial = self.adam.serial
        adam_4068_address = self.adam.address
        adam_4068_available = True
        try:
            adam_interface = ADAMInterface(adam_serial)
            adam_4068 = ADAM_4068(adam_interface, adam_4058_address)
            logging.info("ADAM Modules detected")
        except NameError:
            logging.warning("No ADAM 4068 module available!")
            adam_4068_available = False
         
        boot_pin = config.get("boot_pin")
        pwr_pin = config.get("pwr_pin")

        # --------------------
        # Set up state
        # 

        self.state = UUTState()
        self.bootpin = BootPin(adam_4068, boot_pin)
        self.power = PowerPin(adam_4068, pwr_pin)
        self.backlight = PowerPin(adam_4068, 0)

        self.lock = RLock()

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
def __onchangestate(e):
    logging.debug("\'{0}\': \'{1}\' to \'{2}\'.".format( e.event, e.src, 
        e.dst ))

class PowerPin(fysom.Fysom,):

    def __init__(self, adam_4068, relay_pin):
        fysom.Fysom.__init__(self, {
            'initial' : 'poweroff',
            'events' : [

                { 'name' : 'poweroff', 
                    'src' : [ 'on', ],
                    'dst' : 'off' },

                { 'name' : 'poweron', 
                    'src' : 'off', 
                    'dst' : 'on' },

                ],
            'callbacks' : {
                'onchangestate' : __onchangestate,
                'onenteron' : self.__power_up,
                'onenteroff' : self.__power_down,
                },
            } )

        self.relay = adam_4068
        self.relay_pin_list = [relay_pin]
    
    def __power_up(self, e):
        if self.isstate("off"):
            self.relay.set_digital(self.relay_pin_list, 1)

    def __power_down(self, e):
        if self.isstate("on"):
            self.relay.set_digital(self.relay_pin_list, 0)

class BootPin(fysom.Fysom,):

    def __init__(self, adam_4068, relay_pin):
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
                'onchangestate' : __onchangestate,
                'onenternfd' : self.__disable,
                'onenternfe' : self.__enable,
                },
            } )
     
        self.relay      = adam_4068
        self.relay_pin_list  = [relay_pin]
    
    def __enable(self,):
        if self.isstate("nfd"):
            self.relay.set_digital(self.relay_pin_list, 1)

    def __disable(self,):
        if self.isstate("nfd"):
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
                'onchangestate' : __onchangestate,
                },
            } )

