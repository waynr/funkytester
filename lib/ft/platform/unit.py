#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

## @package unit
#
#  Provides abstractions necessary to represent a whole "Unit Under Test" using
#  various interfaces.
#

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
        INIT        = 0x000001
        ACTIVE      = 0x000002
        POWER       = 0x000004

        BOOTL       = 0x100000
        LINUX       = 0x200000

        BOOT_NFS    = 0x000010
        BOOT_FLASH  = 0x000020
        BOOTING     = 0x000040

        READY       = 0x000080

        LOAD_TESTS  = 0x000100
        TESTING     = 0x000200
        LOAD_BL     = 0x000400
        LOAD_KFS    = 0x000800

        FAIL        = 0x008000

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

        self.options = parent.options
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
        self.activate()

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

    ## Indicate that the UUT is an active Platform Object.
    #
    def activate(self):
        self._fire_status(UnitUnderTest.State.INIT, False)
        self._fire_status(UnitUnderTest.State.ACTIVE)

    ## Perform all the steps necessary to make current UUT "inactive".
    #
    def deactivate(self):
        # power down
        self.powerdown()

        # remove references to Tests
        for test in self.tests[::-1]:
            test.destroy()
            self.tests.remove(test)

        # somehow notify UI to remove reference to Test and Action objects if
        # they don't have associated database entries.
        #
        #  * maybe convert them each to respective TestDB and ActionDB objects?
        #    * best to do this in the UI code itself?

        # status notification
        self._fire_status(UnitUnderTest.State.ACTIVE, False)

    def powerdown(self):
        self.platform_slot.powerdown()
        self.status = UnitUnderTest.State.ACTIVE

    def powerup(self):
        self.platform_slot.powerup()
        self._fire_status(UnitUnderTest.State.POWER)

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

    def _load_bootloader(self):
        pass

    ## Power on the UUT and prepare the U-Boot environment using template script.
    #  
    #  Will always power down, then power up the UUT before attempting to work
    #  the u-boot environment.
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

        self.deactivate()
        self.powerup()
        self.activate()

        # listen for U-Boot prompt
        if not interface.chk(10):
            raise Exception("U-Boot prompt not found!")

        self._fire_status(UnitUnderTest.State.BOOTL)
        self._fire_status(UnitUnderTest.State.READY, False)

        # run given uboot template line-by-line at uboot prompt
        for command in commands:
            if len(command) > 0:
                interface.cmd(command)

        # set UUT's IP address
        self.ip_address = interface.get_var("ipaddr")
        logging.debug(self.ip_address)

        self._fire_status(UnitUnderTest.State.READY)

    def _nfs_test_boot(self):
        self._fire_status(UnitUnderTest.State.BOOT_NFS)
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
        self._fire_status(UnitUnderTest.State.BOOTING)
        self._fire_status(UnitUnderTest.State.BOOTL, False)
        
        # run boot command
        interface = self.interfaces["uboot"]

        interface.cmd("run boot-test", prompt="sh-3.2#", timeout=40)

        self._fire_status(UnitUnderTest.State.READY |
                UnitUnderTest.State.LINUX)
        self._fire_status(UnitUnderTest.State.BOOTING, False)

    ## Initialize UUT's Test objects; if UUT is not booted, boot it to nfs.
    #
    def _initialize_tests(self):
        if not (self.status & (UnitUnderTest.State.LINUX |
            UnitUnderTest.State.BOOT_NFS)):
            self._nfs_test_boot()

        while not self.status & UnitUnderTest.State.READY:
            logging.debug("Not ready.")
            time.sleep(0.1)

        self._fire_status(UnitUnderTest.State.LOAD_TESTS)
        interface = self.interfaces["linux"]

        # run xmlrpc server on remote machine
        xmlrpc_trace = ""
        if self.options and self.options.debug > 0:
            xmlrpc_trace = "-P "
        interface.cmd("./bin/xmlrpcserver.py {0}-p 8001 {1} &".format( 
            xmlrpc_trace, self.ip_address))

        # time out 5 seconds to give xmlrpc server a chance to load and become
        # ready to respond
        time.sleep(5)
        
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

        self._fire_status(UnitUnderTest.State.READY)
        self._fire_status(UnitUnderTest.State.LOAD_TESTS, False)

    ## Run all tests; if tests are not initialized, initialize them.
    #
    def _run_all_tests(self):
        if len(self.tests) == 0:
            self.fire( ft.event.UpdateStatus,
                    obj = self,
                    message = "WARNING: No tests available!",
                    )
        self._fire_status(UnitUnderTest.State.TESTING)
        for test in self.tests:
            test.run()
        self._fire_status(UnitUnderTest.State.READY)

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

            if len(self.tests) == 0:
                self._initialize_tests()

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
    
        @staticmethod
        def remove(uut, data):
            uut.powerdown()
            uut.deactivate()

