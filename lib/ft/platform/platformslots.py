#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import threading, sys, logging, os.path as path, weakref

from sqlalchemy import ( Column, Integer, String, Boolean, DateTime, Text,
        ForeignKey )
from sqlalchemy.orm import relationship
from ft import Base

import ft.event
from ft.platform.unit import UnitUnderTest
from ft.platform.product import Product
from ft.command import Commandable

from eserial import EnhancedSerial

class PlatformSlotDB(Base):

    __tablename__ = "pyft_platform_slot"
    id = Column(Integer, primary_key=True)
    name = Column(String(20))
    hardware_rev = Column(String(50))
    
    platform_id = Column(Integer, ForeignKey('pyft_platform.id'))

    uuts = relationship("UnitUnderTest")

    class Status:
        INIT = "Initialized"
        BUSY = "Busy"
        EMPTY = "Empty"

class PlatformSlot(PlatformSlotDB, Commandable):

    def __init__(self, slot_config, parent):
        self.config = slot_config

        self.address = None
        self.product = Product( self.config["product_manifest_filename"] )
        self.hardware_rev = None
        self.status = PlatformSlot.Status.INIT

        self.__serial = None

        self.parent = parent
        self.lock = threading.RLock()

    def set_address(self, address):
        self.address = (self.parent.address, address)
        self.fire(ft.event.PlatformSlotInit,
                obj = self,
                name = self.name,
                status = self.status,
                )

    def get_serialport(self):
        return weakref.ref(self.__serial)

    def fire(self, event, **kwargs):
        self.parent.fire(event, **kwargs)

    def configure(self, specification_name):
        self.product.set_specification(specification_name)
        self.product.configure()
        self.status = PlatformSlot.Status.EMPTY
        self.__serial = EnhancedSerial(
                self.config["control"]["com"]["serial"],
                self.product.config.serial["baud"],
                )
        self.fire(ft.event.PlatformSlotReady,
            obj = self,
            status = self.status,
            )

    ## Adds a UUT to the FTPlatform
    #
    #  @param serial_number The new unit under test's serial number. 
    #
    #  @param slot This represents the physical slot on the test where the
    #  device resides. This is associated directly with a list of configuration
    #  directives found in the platform configuration whenever FTPlatform is set
    #  up.
    #
    def _create_uut(self, serial_number):
        self.uut = UnitUnderTest(self.config, self)
        self.uut.set_address(serial_number)
        self.uut.configure(serial_number, self.product)

    # - - - - - - - - - - - - - - - - -
    # PlatformSlot commands
    #

    class CommandsSync:
        @staticmethod
        def acknowledge(platform_slot, data):
            return data, ""

        @staticmethod
        def get_manifest(platform_slot, data):
            product = platform_slot.product
            product_list = product.manifest["repositories"]
            return product_list, ""

        @staticmethod
        def set_product_version(platform_slot, data):
            product = platform_slot.product
            product.select(data)
            platform_slot.fire(ft.event.UpdateStatus,
                    message = "Retrieving specification list.",
                    )
            spec_list = product.get_spec_menu_list()
            return spec_list, ""

        @staticmethod
        def select_product(platform_slot, data):
            product_name = data
            product = platform_slot.product
            repository_list = product.manifest["repositories"]
            selected = None
            for repository in repository_list:
                if repository["name"] == product_name:
                    selected = repository
                    break
            if not selected:
                return None, "ERROR: Invalid product selection"
            product.set_info(repository)
            refs = product.get_product_versions()
            return refs, ""

        @staticmethod
        def set_product_specification(platform_slot, data):
            platform_slot.product.set_specification(data)
            return None, ""

    class CommandsAsync:
        @staticmethod
        def acknowledge(platform_slot, data):
            pass

        @staticmethod
        def set_uut_serialnum(platform_slot, serialnum):
            platform_slot._create_uut(serialnum)
            return None, ""

        @staticmethod
        def configure(platform_slot, data):
            platform_slot.configure(data)
            return None, ""

