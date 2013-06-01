#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import logging

import gtk

from ft.platform import UnitUnderTest
from ft.test import Test, Action

class ManagerMenu(gtk.Menu):

    def __init__(self, *args, **kwargs):
        super(ManagerMenu, self).__init__(*args, **kwargs)
        self.adapter = None

    def _popup(self, adapter, button, activate_time):
        self.adapter = adapter
        super(ManagerMenu, self).popup(None, None, None, button, activate_time)

class UUTManagerMenu(ManagerMenu):

    def __init__(self, *args, **kwargs):
        super(UUTManagerMenu, self).__init__(*args, **kwargs)
        self.__init_menuitems()

    def popup(self, adapter, *args, **kwargs):
        #if adapter.status == UnitUnderTest.Status.
        super(UUTManagerMenu, self)._popup(adapter, *args, **kwargs)

    def __init_menuitems(self):
        self.nfs_test_boot = gtk.MenuItem("NFS Quick Boot")
        self.nfs_test_boot.connect('activate', self.__nfs_test_boot_cb)
        self.nfs_test_boot.show()

        self.nfs_full_boot = gtk.MenuItem("NFS Full Boot")
        self.nfs_full_boot.connect('activate', self.__nfs_full_boot_cb)
        self.nfs_full_boot.show()

        self.onboard_flash_boot = gtk.MenuItem("Onboard Flash Boot")
        self.onboard_flash_boot.connect('activate',
                self.__onboard_flash_boot_cb)
        self.onboard_flash_boot.show()

        self.run_all_tests = gtk.MenuItem("Run All Tests")
        self.run_all_tests.connect('activate',
                self.__run_all_tests_cb)
        self.run_all_tests.show()

        self.load_kfs = gtk.MenuItem("Load KFS")
        self.load_kfs.connect('activate', self.__load_bootloader_cb)
        self.load_kfs.show()
        self.load_kfs.set_sensitive(False)

        self.load_bootloader = gtk.MenuItem("Load Bootloader")
        self.load_bootloader.connect('activate', self.__load_bootloader_cb)
        self.load_bootloader.show()
        self.load_bootloader.set_sensitive(False)

        self.load_kfs = gtk.MenuItem("Load Kernel+Filesystem")
        self.load_kfs.connect('activate', self.__load_kfs_cb)
        self.load_kfs.show()
        self.load_kfs.set_sensitive(False)

        self.log_data = gtk.MenuItem("Log Data")
        self.log_data.connect('activate', self.__log_data_cb)
        self.log_data.show()
        self.log_data.set_sensitive(False)

        self.s1 = gtk.SeparatorMenuItem()
        self.s1.show()
        self.s2 = gtk.SeparatorMenuItem()
        self.s2.show()
        self.s3 = gtk.SeparatorMenuItem()
        self.s3.show()

        self.append(self.nfs_test_boot)
        self.append(self.nfs_full_boot)
        self.append(self.onboard_flash_boot)
        self.append(self.s1)
        self.append(self.run_all_tests)
        self.append(self.s2)
        self.append(self.load_bootloader)
        self.append(self.load_kfs)
        self.append(self.s3)
        self.append(self.log_data)

    def __nfs_test_boot_cb(self, menuitem):
        self.adapter.run_command(('nfs_test_boot', None, False))

    def __nfs_full_boot_cb(self, menuitem):
        self.adapter.run_command(('nfs_full_boot', None, False))

    def __onboard_flash_boot_cb(self, menuitem):
        self.adapter.run_command(('onboard_flash_boot', None, False))

    def __run_all_tests_cb(self, menuitem):
        self.adapter.run_command(('run_all_tests', None, False))

    def __load_bootloader_cb(self, menuitem):
        self.adapter.run_command(('load_bootloader', None, False))

    def __load_kfs_cb(self, menuitem):
        self.adapter.run_command(('load_kfs', None, False))

    def __log_data_cb(self, menuitem):
        self.adapter.run_command(('log_data', None, False))

class TestManagerMenu(ManagerMenu):

    def __init__(self, *args, **kwargs):
        super(TestManagerMenu,  self).__init__(*args, **kwargs)

        self.__init_menuitems()

    def popup(self, adapter, *args, **kwargs):

        super(TestManagerMenu, self)._popup(adapter, *args, **kwargs)

    def __init_menuitems(self):
        self.run = gtk.MenuItem("Run")
        self.run.connect('activate', self.__run_cb)
        self.run.show()

        self.append(self.run)

    def __run_cb(self, menuitem):
        self.adapter.run_command(('run', None, False))
        
class ActionManagerMenu(ManagerMenu):

    def __init__(self, *args, **kwargs):
        super(ActionManagerMenu, self).__init__(*args, **kwargs)
    
    def popup(self, adapter, *args, **kwargs):

        super(ActionManagerMenu, self)._popup(adapter, *args, **kwargs)

