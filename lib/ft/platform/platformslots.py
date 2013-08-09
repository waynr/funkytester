#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import time

import threading, sys, logging, os.path as path, weakref, os

from sqlalchemy import ( Column, Integer, String, Boolean, DateTime, Text,
        ForeignKey )
from sqlalchemy.orm import relationship
from ft import Base

import ft.event
from ft.platform.unit import UnitUnderTest
from ft.platform.product import Product
from ft.platform.controller import Relay, UUTState
from ft.command import Commandable

from eserial import EnhancedSerial
from interfaces import adam, ADAM_4068

class PlatformSlotDB(Base):

    __tablename__ = "pyft_platform_slot"
    id = Column(Integer, primary_key=True)
    name = Column(String(20))
    hardware_rev = Column(String(50))
    
    platform_id = Column(Integer, ForeignKey('pyft_platform.id'))

    uuts = relationship("UnitUnderTest")

    class State:
        INIT        = 0x0000
        OCCUPIED    = 0x0001
        POWER       = 0x0002

class PlatformSlot(PlatformSlotDB, Commandable):

    def __init__(self, slot_config, parent):
        self.config = slot_config
        self.options = parent.options

        self.address = None
        self.product = Product( self.config["product_manifest_filename"] )
        self.hardware_rev = None
        self.status = PlatformSlot.State.INIT

        self.__serial = None
        self.__control = {}

        self.platform = parent
        self.event_handler = parent.event_handler

        self.lock = threading.RLock()

    def set_address(self, address):
        self.address = (self.platform.address, address)
        self.fire(ft.event.PlatformSlotInit,
                obj = self,
                name = self.name,
                status = self.status,
                )

    def get_serialport(self):
        return weakref.ref(self.__serial)

    def fire(self, event, **kwargs):
        self.event_handler.fire(event, **kwargs)

    def _fire_status(self, state_bit=None, on=True):
        if state_bit:
            if on:
                self.status |= state_bit
            elif not on:
                self.status &= ~state_bit

        self.fire(ft.event.PlatformSlotEvent,
                obj = self,
                status = self.status,
                datetime = time.time()
                )

    def configure(self, specification_name):
        self.product.set_specification(specification_name)
        self.product.configure()

        if False:
            self._deploy_files()

        self.__serial = EnhancedSerial(
                self.config["control"]["com"]["serial"],
                self.product.config.serial["baud"],
                )
        self.__serial.start()

        # Hard-code adam module initialization for now, but keep modularity in
        # mind for later feature implementation.
        #
        self.__init_adam()
        #try:
            #self.__init_adam()
        #except:
            #message = "ADAM Module initialization failed!"
            #self.fire(ft.event.UpdateStatus,
                    #obj = self,
                    #message = message,
                    #)

        self.status = PlatformSlot.State.INIT
        self.fire(ft.event.PlatformSlotReady,
            obj = self,
            status = self.status,
            )

    def _deploy_files(self):
        product_tftp_dir = os.path.join(self.product.local_path, "tftp_files")
        platform_tftp_dir = os.path.join(self.platform.config.tftp_base_dir,
                self.product.config.uboot["tftp_dir"])
        for dirpath, dirnames, filenames in os.walk(tftp_filedir):
            for filename in filenames:
                filename = os.path.join(dirpath, filename)
                self.platform.deploy_tftp(platform_tftp_dir, filename)

        self.platform.deploy_nfs(self.product)

    def __init_adam(self):
        adam_dict = self.config["control"]["adam"]
        adam_4068_address = adam_dict["address"]
        adam_4068_available = True
        try:
            adam_interface = adam.get_adam_interface()
            adam_4068 = ADAM_4068(adam_interface, adam_4068_address)
            logging.info("ADAM Modules detected")
            self.__init_control(adam_4068, adam_dict["pins"])
        except NameError:
            adam_4068_available = False
            raise

    ## Initialize the control interface for this PlatformSlot.
    #
    #  @interface Some kind of controller interface accepted by the "Relay"
    #  class that can toggle values to "on" or "off" states, for instance
    #  switching a relay to 'on' would toggle the power of some embedded system
    #  to activate it.
    #
    #  @control_config A dictionary with keys whose names indicate the
    #  funtionality of the control function being performed and whose values are
    #  lists of integers indicating which values/indices on the given interface
    #  are of interest.
    #
    def __init_control(self, interface, control_config):
        for key, pinlist in control_config.items():
            self.__control[key] = Relay(interface, pinlist)

    def get_control(self):
        return self.__control

    def powerdown(self):
        self.lock.acquire()
        if self.__control.has_key("power"):
            if self.__control["power"].isstate("off"):
                self.fire( ft.event.UpdateStatus, 
                        message = "INFO: Unit already powered down.",
                        )
            else:
                self.__control["power"].disable()
                if self.__control.has_key("backlight"):
                    self.__control["backlight"].disable()
                self._fire_status(PlatformSlot.State.POWER, False)

        else:
            self.fire( ft.event.UpdateStatus,
                    message = "WARNING: Automated powerdown not available.",
                    )

        self.lock.release()

    def powerup(self):
        self.lock.acquire()
        if self.__control.has_key("power"):
            if self.__control["power"].isstate("on"):
                self.fire( ft.event.UpdateStatus, 
                        message = "INFO: Unit already powered up.",
                        )
            else:
                self.__control["power"].enable()
                if self.__control.has_key("backlight"):
                    self.__control["backlight"].enable()
                self._fire_status(PlatformSlot.State.POWER)
        else:
            self.fire( ft.event.UpdateStatus, 
                    message = "WARNING: Automated powerup not available.",
                    )

        self.lock.release()

    ## Adds a UUT to the FTPlatform
    #
    #  @param data A structure containing data about the UUT passed in from the
    #  UI.
    #
    #  @param slot This represents the physical slot on the test where the
    #  device resides. This is associated directly with a list of configuration
    #  directives found in the platform configuration whenever FTPlatform is set
    #  up.
    #
    def _create_uut(self, data):
        self.lock.acquire()
        serial_number = data["serialnum"]

        if self.status & PlatformSlot.State.OCCUPIED:
            self._fire_status()
            self.fire( ft.event.UpdateStatus,
                    message = "WARNING: PlatformSlot currently populated.",
                    )
            return

        self.uut = UnitUnderTest(self.config, self, serial_number)
        self.uut.set_address(serial_number)
        self.uut.configure(serial_number, self.product)

        self.platform.uuts[serial_number] = self.uut
        
        self._fire_status(PlatformSlot.State.OCCUPIED)
        self.fire( ft.event.PlatformSlotEvent, 
                obj = self,
                current_uut = serial_number,
                product_type = self.product.name,
                metadata_version = self.product.metadata_version,
                specification_name = self.product.specification_name,
                )
        self.powerdown()

        self.lock.release()

    ## Remove the current UUT object.
    #
    def _clear_uut(self):
        self.uut.deactivate()
        self._fire_status(PlatformSlot.State.OCCUPIED, False)
        self.fire( ft.event.PlatformSlotEvent,
                obj = self,
                current_uut = "",
                )

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
        def set_uut(platform_slot, data):
            platform_slot._create_uut(data)
            return None, ""

        @staticmethod
        def clear_uut(platform_slot, data):
            platform_slot._clear_uut()
            return None, ""

        @staticmethod
        def configure(platform_slot, data):
            platform_slot.configure(data)
            return None, ""
    
        @staticmethod
        def power_up(platform_slot, data):
            platform_slot.uut.powerup()

        @staticmethod
        def power_down(platform_slot, data):
            platform_slot.uut.powerdown()

