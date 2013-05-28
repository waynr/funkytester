#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import gtk, logging

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
        #if adapter.status == 
        super(UUTManagerMenu, self)._popup(adapter, *args, **kwargs)

    def __init_menuitems(self):
        self.run_all = gtk.MenuItem("Run All")
        self.run_all.connect('activate', self.__runall_cb)

        self.log_data = gtk.MenuItem("Log Data")
        self.log_data.connect('activate', self.__logdata_cb)

        self.power_up = gtk.MenuItem("Power Up")
        self.power_up.connect('activate', self.__powerup_cb)
        self.power_up.show()

        self.power_down = gtk.MenuItem("Power Down")
        self.power_down.connect('activate', self.__powerdown_cb)

        self.append(self.run_all)
        self.append(self.log_data)
        self.append(self.power_up)
        self.append(self.power_down)

    def __runall_cb(self, menuitem):
        logging.debug("blah blah blah")

    def __logdata_cb(self, menuitem):
        pass

    def __powerup_cb(self, menuitem):
        self.adapter.run_command(('power_up', None, False))
        self.power_down.show()
        self.power_up.hide()

    def __powerdown_cb(self, menuitem):
        self.adapter.run_command(('power_down', None, False))
        self.power_up.show()
        self.power_down.hide()

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

