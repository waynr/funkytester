#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

## @package unit
#
#  Provides abstractions necessary to represent a whole "Unit Under Test" using
#  various interfaces.
#

import logging, threading

from sqlalchemy import ( Column, Integer, String, Boolean, DateTime, Text,
        ForeignKey )
from sqlalchemy.orm import relationship

from interfaces import (
        xmlrpc,
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
    serial_number = Column(String(20))
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
        self.serial_number = serial_number
        self.product = None
        self.mac_address = None
        self.ip_address = None
        self.status = self.Status.INIT

        self.com = config["control"]["com"]
        self.adam = config["control"]["adam"]

        self.parent = parent

        self.lock = threading.RLock()

    def set_address(self, serial_number):
        self.address = (self.parent.address, serial_number)
        self.fire( ft.event.UUTInit,
                obj = self,
                name = self.serial_number,
                status = self.status,
                )

    def fire(self, event, **kwargs):
        self.parent.fire(event, **kwargs)

    def configure(self, serial_number, product, mac_address=None):
        self.serial_number = serial_number
        self.product = product
        self.mac_address = mac_address

        self.serial = self.parent.get_serialport()
        self.control = self.parent.get_control()
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
                name = self.serial_number,
                status = self.status,
                )

    def __load_testlist(self):
        self.testlist = list()

        for test_dict in self.specification["testlist"]:
            newtest = Test(test_dict, self, None)
            self.testlist.append(newtest)

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

