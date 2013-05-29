#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

## @package unit
#
#  Provides abstractions necessary to represent a whole "Unit Under Test" using
#  various interfaces.
#

import logging, threading
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

    class Status:
        INIT = "Initialized"

        LISTENING = "Listening"
        WAITING = "Waiting"

        NFS_BOOTING = "Booting NFS Test"
        NFS_WAITING = "NFS Waiting"
        NFS_LOADING = "NFS Loading Tests"
        NFS_TESTING = "Testing"

        LOAD_KFS = "Loading Kernel & Filesystem"
        LOAD_BOOTLOADER = "Loading Bootloader"

        BOOTING_LOCAL = "Booting Local FS"
        TEST_FIRSTBOOT = "First Boot"

        PASS = "Pass"
        FAIL = "Fail"

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

        self.platform_slot = parent

        self.lock = threading.RLock()

    def set_address(self, serial_number):
        self.address = (self.platform_slot.address, serial_number)
        self.fire( ft.event.UUTInit,
                obj = self,
                name = self.serial_number,
                status = self.status,
                )

    def fire(self, event, **kwargs):
        self.platform_slot.fire(event, **kwargs)

    def configure(self, serial_number, product, mac_address=None):
        self.serial_number = serial_number
        self.product = product
        self.mac_address = mac_address

        self.serial = self.platform_slot.get_serialport()
        self.interfaces = { 
                "linux" : LinuxTerminalInterface(
                    prompt = self.product.config.prompt["linux"]["standard"],
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
    def run_all(self):
        self._load_bootloader()
        self._run_nfs_test()
        self._load_kfs()
        self._run_firstboot()

    def _load_bootloader(self):
        pass

    def _run_nfs_test(self):
        self.status = UnitUnderTest.Status.NFS_BOOTING
        self.fire( ft.event.UnitUnderTestEvent,
                obj = self,
                status = self.status,
                )
        # get nfs_test.template from product
        template_string = self.product.get_template("nfs_test.template")
        
        # initialize template object 
        template = Template(template_string)
        
        # get 'uboot' portion of product config as mapping
        mapping_dict = self.product.config.uboot
        platform = self.platform_slot.platform
        mapping_dict["server_ip"] = platform.config.server_ip
        mapping_dict["gateway_ip"] = platform.config.gateway_ip
        mapping_dict["baud"] = self.product.config.serial["baud"]

        # substitute mapping into template
        script = template.substitute(mapping_dict)

        # split template into list of commands
        commands = script.split("\n")
        
        # poweron the slot
        interface = self.interfaces["uboot"]
        self.platform_slot.powerup()

        # listen for U-Boot prompt
        if not interface.chk(10):
            raise Exception("U-Boot prompt not found!")

        # run list of commands at U-Boot prompt
        for command in commands:
            interface.cmd(command)

        # run list of commands at U-Boot prompt
        self.ip_addr = interface.get_var("ip_addr")

        # run boot command
        interface.cmd("run boot-test")

        interface = self.interface["linux"]
        interface.login()

        self.status = UnitUnderTest.Status.NFS_WAITING
        self.fire( ft.event.UUTEvent,
                obj = self,
                status = self.status,
                )
        # run xmlrpc server on remote machine
        interface.cmd("./bin/xmlrpcserver.py {0}".format(uut_ip_addr))
        
        # initialize xmlrpc client
        def load_xmlrpc_client():
            try:
                xmlrpc_client = xmlrpclib.ServerProxy("http://{0}:{1}".format(
                    uut_ip, "8000"), allow_none=True)
            except Exception:
                logging.warning("XML RPC Client Failed to connect, "\
                        "waiting 2 then trying again.")
                time.sleep(2)
                xmlrpc_client = load_xmlrpc_client()
            return xmlrpc_client

        xmlrpc_client = load_xmlrpc_client()

        # initialize Tests from Product's Specification and xmlrpc client
        specification_dict = self.product.specification.test_spec
        self.tests = []

        self.status = UnitUnderTest.Status.NFS_LOADING
        self.fire( ft.event.UUTEvent,
                obj = self,
                status = self.status,
                )
        for i, test_dict in enumerate(specification_dict["testlist"]):
            self.tests.append(Test(test_dict, self, xmlrpc_client))
            self.tests[i].set_address(i)

        self.status = UnitUnderTest.Status.NFS_TESTING
        self.fire( ft.event.UUTEvent,
                obj = self,
                status = self.status,
                )
        for test in self.tests:
            test.run()

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
        def run_all(uut, data):
            uut.run_all()

