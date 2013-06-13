#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

## @package unit
#
#  Provides abstractions necessary to represent a whole "Unit Under Test" using
#  various interfaces.
#

import time

import logging, threading, time, xmlrpclib
from string import Template

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

    class State:
        INIT        = 0x0000
        POWER       = 0x0002

        UBOOT       = 0x0004
        LINUX       = 0x0008

        BOOT_NFS    = 0x0010
        BOOT_FLASH  = 0x0020

        BOOTING     = 0x0040
        WAITING     = 0x0080

        LOAD_TESTS  = 0x0100
        TESTING     = 0x0200
        LOAD_BL     = 0x0400
        LOAD_KFS    = 0x0800

        FAIL        = 0x8000

    def __repr__(self,):
        rstring = "<UnitUnderTest('%s','%s','%s')>" 
        rtuple = self.name, self.serial_number, self.status
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
        self.status = self.State.INIT

        self.name = "Anonymous Unit"

        self.com = config["control"]["com"]

        self.platform_slot = parent
        self.event_handler = parent.event_handler

        self.lock = threading.RLock()

    def set_address(self, serial_number):
        self.address = (self.platform_slot.address, serial_number)
        self.fire( ft.event.UUTInit,
                obj = self,
                name = self.serial_number,
                status = self.status,
                )

    def fire(self, event, **kwargs):
        self.event_handler.fire(event, **kwargs)

    def _fire_status(self, state_bit=None, on=True):
        if state_bit:
            if on:
                self.status |= state_bit
            elif not on:
                self.status &= ~state_bit

        self.fire(ft.event.UnitUnderTestEvent,
                obj = self,
                status = self.status,
                datetime = time.time()
                )

    def configure(self, serial_number, product, mac_address=None):
        self.serial_number = serial_number
        self.product = product
        self.mac_address = mac_address

        self.name = product.name

        self.serial = self.platform_slot.get_serialport()
        self.interfaces = { 
                "linux" : LinuxTerminalInterface(
                    prompt = self.product.config.prompt["linux"]["test"],
                    enhanced_serial = self.serial(),
                    ),
                "uboot" : UBootTerminalInterface(
                    prompt = self.product.config.prompt["uboot"],
                    enhanced_serial = self.serial(),
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

    ## Run all selected test modes.
    #
    def run_all_modes(self):
        self._load_bootloader()
        self._run_nfs_test()
        self._load_kfs()
        self._run_firstboot()

    def _load_bootloader(self):
        pass

    def _run_nfs_test(self):
        self._boot_nfs_test()
        self._initialize_tests()
        self._run_all_tests()

    ## Power on the UUT and prepare the U-Boot environment using template script.
    #
    # @param template_string Python Template string.
    # @param mapping Dictionary object whose keys correspond to variables to be
    # interpolated in the "template_string".
    # @param kwargs Contains additional key-value pairs to be added to the
    # "mapping" object.
    #
    def __uboot_prep(self, template_string, mapping, **kwargs):
        for key, value in kwargs.items():
            mapping[key] = value

        # initialize template object 
        template = Template(template_string)
        
        # substitute mapping into template
        script = template.substitute(mapping)

        # split template into list of commands
        commands = script.split("\n")

        # poweron the slot
        interface = self.interfaces["uboot"]
        self.platform_slot.powerup()

        # listen for U-Boot prompt
        if not interface.chk(10):
            raise Exception("U-Boot prompt not found!")

        # run given uboot template line-by-line at uboot prompt
        for command in commands:
            if len(command) > 0:
                interface.cmd(command)

        # set UUT's IP address
        self.ip_address = interface.get_var("ipaddr")
        logging.debug(self.ip_address)

    def _nfs_test_boot(self):
        self._fire_status(~UnitUnderTest.State.BOOT_NFS, False)

        # get nfs_test.template from product
        template_string = self.product.get_file("nfs_test.template")
        
        # get 'uboot' portion of product config as mapping
        mapping_dict = self.product.config.uboot
        platform = self.platform_slot.platform

        # pass in template string, mapping dict, and additional values to be
        # added to the mapping dict, get interface object back
        self.__uboot_prep(template_string, mapping_dict, 
            server_ip = platform.config.server_ip,
            gateway_ip = platform.config.gateway_ip,
            nfs_base_dir = platform.config.nfs_base_dir,
            baud = self.product.config.serial["baud"],
            )
        
        # run boot command
        interface = self.interfaces["uboot"]
        self._fire_status(~UnitUnderTest.State.BOOTING, False)

        interface.cmd("run boot-test", prompt="sh-3.2#", timeout=40)

        self._fire_status(UnitUnderTest.State.UBOOT, False)
        self._fire_status(UnitUnderTest.State.WAITING |
                UnitUnderTest.State.LINUX)

    ## Initialize UUT's Test objects; if UUT is not booted, boot it to nfs.
    #
    def _initialize_tests(self):
        if not (self.status & (UnitUnderTest.State.WAITING |
            UnitUnderTest.State.LINUX)):
            self._nfs_test_boot()

        interface = self.interfaces["linux"]

        # run xmlrpc server on remote machine
        interface.cmd("./bin/xmlrpcserver.py -p 8001 {0} &".format( 
            self.ip_address))
        
        # initialize xmlrpc client
        xmlrpc_server_address = "http://{0}:{1}".format(self.ip_address, "8001")
        def load_xmlrpc_client():
            try:
                xmlrpc_client = xmlrpclib.ServerProxy(xmlrpc_server_address,
                        allow_none=True)
            except Exception:
                import traceback
                logging.warning("XML RPC Client Connection Failure: {0}".format(
                    xmlrpc_server_address))
                logging.warning(traceback.format_exc())
                time.sleep(2)
                xmlrpc_client = load_xmlrpc_client()
            return xmlrpc_client

        xmlrpc_client = load_xmlrpc_client()

        logging.debug("XML RPC Client Loaded for: {0}".format(
            xmlrpc_server_address))

        # initialize Tests from Product's Specification and xmlrpc client
        specification_dict = self.product.specification
        self.tests = []

        for i, test_dict in enumerate(specification_dict["testlist"]):
            test = Test(test_dict, self, xmlrpc_client)
            test.set_address(i)
            test.initialize_actions()
            self.tests.append(test)

        self._fire_status(UnitUnderTest.State.LOAD_TESTS |
                UnitUnderTest.State.WAITING)

    ## Run all tests; if tests are not initialized, initialize them.
    #
    def _run_all_tests(self):
        if not self.status & UnitUnderTest.State.LOAD_TESTS:
            self._initialize_tests()

        if len(self.tests) == 0:
            self.fire( ft.event.UpdateStatus,
                    obj = self,
                    message = "WARNING: No tests available!",
                    )
        self._fire_status(UnitUnderTest.State.TESTING)
        for test in self.tests:
            test.run()
        self._fire_status(UnitUnderTest.State.WAITING)

    def _load_kfs(self):
        pass

    def _run_firstboot(self):
        pass

    ## Boot into NFS Filesystem.
    #
    def _nfs_boot(self):
        pass
    
    class CommandsSync:
        @staticmethod
        def acknowledge(uut, data):
            return data, ""

    class CommandsAsync:
        @staticmethod
        def acknowledge(uut, data):
            pass

        @staticmethod
        def nfs_test_boot(uut, data):
            uut._nfs_test_boot()
            uut._initialize_tests()

        @staticmethod
        def nfs_full_boot(uut, data):
            pass

        @staticmethod
        def onboard_flash_boot(uut, data):
            pass

        @staticmethod
        def run_all_tests(uut, data):
            uut._run_all_tests()

        @staticmethod
        def load_bootloader(uut, data):
            pass

        @staticmethod
        def load_kfs(uut, data):
            pass

        @staticmethod
        def log_data(uut, data):
            pass

        @staticmethod
        def run_all_modes(uut, data):
            uut._run_all_modes()

