#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

## @package platform
#
#  Abstraction representing a physical test platform and the capabilities it
#  offers through its configuration file. There are at least four test platforms
#  in the works:
#   
#   * GE Functional Tester
#   * EMAC Quad SOM200 Tester
#   * TestPC Tester
#   * Individual Product
#

import threading, sys, logging, os.path as path, subprocess, shlex, os, shutil

from sqlalchemy import ( Column, Integer, String, Boolean, DateTime, Text,
        ForeignKey )
from sqlalchemy.orm import relationship
from ft import Base

import ft.event
from ft.platform.unit import UnitUnderTest
from ft.platform.product import Product
from ft.platform.platformslots import PlatformSlot
from ft.platform.configuration import HasMetadata, GenConfig
from ft.command import Commandable, Command
from ft.util.yaml_util import load_manifest

from interfaces import (
        adam,
        )

class PlatformDB(Base):
    
    __tablename__ = "pyft_platform"
    id = Column(Integer, primary_key=True)
    name = Column(String(20))
    hardware_rev = Column(String(50))
    metadata_repo = Column(String(100))
    metadata_version = Column(String(100))

    platform_slots = relationship("PlatformSlot")
        
    def __repr__(self,):
        rstring = "<Platform('%s','%s','%s':'%s')>" 
        rtuple = ( self.name, self.hardware_rev, self.metadata_repo, 
                self.metadata_version, )
        return rstring % rtuple

class Platform(PlatformDB, HasMetadata, Commandable):

    __metadata_type__ = "platforms"

    def __init__(self, manifest_file, event_handler, address=None):
        HasMetadata.__init__(self) 

        self.config = None
        self.manifest = load_manifest(manifest_file)
        self.metadata_repo_dict = self.manifest["metadata_repo"]
        self.repo = None
        self.local_path = None

        self.address = address
        self.slots = list()
        self.uuts = dict()

        self.event_handler = event_handler
        self.lock = threading.RLock()

        self.commands = Command(self)

        self.fire(ft.event.PlatformInit, 
                obj = self, 
                name = self.name,
                )

    def fire(self, event, **kwargs):
        self.event_handler.fire(event, **kwargs)

    def configure(self):
        config_file = path.join(self.repo.local_path, "config.yaml")
        self.__configure(config_file)
        self.__slots_setup()
        self.__adam_setup()

        self.fire(ft.event.UpdateStatus, 
            obj = self, 
            name = self.name,
            message = ("Platform configured. Address: {0}".format(
                self.address))
            )
        self.fire(ft.event.PlatformReady, 
                obj = self, 
                name = self.name,
                )

    def deploy_nfs(self, product):
        self.fire(ft.event.UpdateStatus,
                obj = self,
                message = "INFO: Deploying NFS archive . . .",
                )
        filesystem_archive = os.path.join(product.local_path,
                product.config.uboot["test_filesystem"])
        dest_dir = os.path.join(self.config.nfs_base_dir,
                product.config.uboot["nfs_dir"])

        cleanup_string = 'sudo -S rm -rf {0}'.format(dest_dir)
        mkdir_string = 'sudo -S mkdir -p {0}'.format(dest_dir)
        tar_string = 'sudo -S tar -pxzf {0} -C {1}'.format(filesystem_archive,
                dest_dir)
        make_string = 'sudo -S make install-nfs'

        for command_string in [cleanup_string, mkdir_string, tar_string,
                make_string]:
            p = subprocess.Popen(shlex.split(command_string), stdin=subprocess.PIPE)
            p.communicate(input=self.config.password)
            p.wait()
            if not p.returncode == 0:
                raise Exception("Command failed: {0}".format(command_string))

        self.fire(ft.event.UpdateStatus,
                obj = self,
                message = "INFO: NFS Achive Deployed . . .",
                )

    def deploy_tftp(self, product, file_path):
        self.fire(ft.event.UpdateStatus,
                obj = self,
                message = "INFO: Deploying TFTP File: {0}".format(file_path),
                )
        dest_dir = os.path.join(self.config.tftp_base_dir,
                product.config.uboot["tftp_dir"])
        try:
            os.makedirs(dest_dir)
        except OSError:
            pass

        try:
            shutil.copy2(file_path, dest_dir)
        except:
            raise
        else:
            self.fire(ft.event.UpdateStatus,
                    obj = self,
                    message = "INFO: TFTP Deploy successful: {0}".format(
                        file_path),
                    )

    def get_platform_versions(self):
        self._setup_repo()
        return self.repo.get_refs()

    def cleanup(self):
        pass

    def __configure(self, config_file):
        self.config = GenConfig(config_file)
        product_manifest_file = path.join(self.repo.local_path, "manifest.yaml")
        self.product_manifest = load_manifest(product_manifest_file)

    def __slots_setup(self):
        self.slots = [None] * len(self.config.slots)
        for i, config in enumerate(self.config.slots):
            config["product_manifest_filename"] = path.join(self.repo.local_path,
                    "manifest.yaml")
            self.slots[i] = PlatformSlot(config, self)
            self.slots[i].set_address(i)
            self.slots[i].product_manifest = self.product_manifest

    ## Configure ADAM Modules' serial ports
    #
    def __adam_setup(self):
        serial = self.config.adam[0]["serial"]
        baud = self.config.adam[0]["baud"]
        adam.get_adam_interface(serial, baud)

    def __native_setup(self):
        pass
    
    ## Ensure that the NFS and TFTP servers are running locally.
    #
    def _server_setup(self):
        nfs_dict = {
                "host": None,
                }
        nfs_dict = {
                "host": None,
                "path": None,
                }
    
    # - - - - - - - - - - - - - - - - -
    # Platform commands
    #

    class CommandsSync:
        @staticmethod
        def is_setup(platform, data):
            return False, ""

        @staticmethod
        def get_manifest(platform, data):
            result = platform.manifest["repositories"]
            return result, ""

        @staticmethod
        def select_platform(platform, data):
            platform_name = data
            repository_list = platform.manifest["repositories"]
            selected = None
            for repository in repository_list:
                if repository["name"] == platform_name:
                    selected = repository
                    break
            if not selected:
                return None, "ERROR: Invalid product selection."
            platform.set_info(repository)
            refs = platform.get_platform_versions()
            return refs, ""

        @staticmethod
        def set_platform_version(platform, data):
            success = platform.repo.checkout(data)
            return success, ""
    
        @staticmethod
        def acknowledge(platform, data):
            return False, ""
    
    class CommandsAsync:
        @staticmethod
        def acknowledge(platform, data):
            pass

        @staticmethod
        def configure(platform, data):
            platform.configure()
            return None, ""
    
