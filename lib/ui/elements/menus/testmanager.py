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
        self.run_all = gtk.MenuItem("NFS Test")
        self.run_all.connect('activate', self.__runall_cb)
        self.run_all.show()

        self.load_kfs = gtk.MenuItem("Load KFS")
        self.load_kfs.connect('activate', self.__logdata_cb)

        self.load_bootloader = gtk.MenuItem("Load Bootloader")
        self.load_bootloader.connect('activate', self.__logdata_cb)

        self.log_data = gtk.MenuItem("Log Data")
        self.log_data.connect('activate', self.__logdata_cb)

        self.append(self.run_all)
        self.append(self.log_data)

    def __runall_cb(self, menuitem):
        self.adapter.run_command(('run_all', None, False))

    def __logdata_cb(self, menuitem):
        pass

class TestManagerMenu(ManagerMenu):

    def __init__(self, *args, **kwargs):
        super(TestManagerMenu,  self).__init__(*args, **kwargs)

        self.__init_menuitems()

    def popup(self, adapter, *args, **kwargs):

        super(UUTManagerMenu, self)._popup(adapter, *args, **kwargs)

    def __init_menuitems(self):
        self.run = gtk.MenuItem("Run")

        self.append(self.run)
        
class ActionManagerMenu(ManagerMenu):

    def __init__(self, *args, **kwargs):
        super(ActionManagerMenu, self).__init__(*args, **kwargs)
    
    def popup(self, adapter, *args, **kwargs):

        super(UUTManagerMenu, self)._popup(adapter, *args, **kwargs)

