#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import logging

import gtk

from testmanager import ManagerMenu
from ft.platform import PlatformSlot

class SlotManagerMenu(ManagerMenu):

    def __init__(self, *args, **kwargs):
        super(ManagerMenu, self).__init__(*args, **kwargs)
        self.__init_menuitems()

    def popup(self, adapter, *args, **kwargs):
        if adapter.status == PlatformSlot.Status.POWERUP:
            self.power_up.hide()
            self.power_down.show()

        if adapter.status == PlatformSlot.Status.POWERDOWN:
            self.power_up.show()
            self.power_down.hide()

        if adapter.status == PlatformSlot.Status.EMPTY:
            self.power_up.hide()
            self.power_down.hide()
            return

        super(SlotManagerMenu, self)._popup(adapter, *args, **kwargs)

    def __init_menuitems(self):
        self.power_up = gtk.MenuItem("Power Up")
        self.power_up.connect('activate', self.__powerup_cb)
        self.power_up.show()

        self.power_down = gtk.MenuItem("Power Down")
        self.power_down.connect('activate', self.__powerdown_cb)
    
        self.append(self.power_up)
        self.append(self.power_down)

    def __powerup_cb(self, menuitem):
        self.adapter.run_command(('power_up', None, False))
        self.power_down.show()
        self.power_up.hide()

    def __powerdown_cb(self, menuitem):
        self.adapter.run_command(('power_down', None, False))
        self.power_up.show()
        self.power_down.hide()

