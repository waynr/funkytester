#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

# Copyright (C) 2012  Wayne Warren (wwarren@emacinc.com)
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
# 
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51 Franklin
# Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
#

import sys, logging

import gtk

from ui.elements.dialogs.selections import AbstractSelectionDialog
from ui.elements.pages.platformslotsetuppage import PlatformSlotSetupPage
from ui.elements.pages.testmanagerpage import TestManagerPage
from ui.elements.adapters import (PlatformAdapter, PlatformSlotAdapter,
        UnitUnderTestAdapter, TestAdapter, ActionAdapter)

from ft.command import RecipientType

class ftw:
    MAX_WIN_WIDTH = 1280
    MAX_WIN_HEIGHT = 700

class FunctionalTestWindow(gtk.Window):

    (SLOT_SETUP,
     TEST_MANAGER ) = range(2)

    def __init__(self, handler):
        gtk.Window.__init__(self)

        self.handler = handler

        self.testmanagermodel = handler.testmanagermodel
        self.slotsmanagermodel = handler.slotsmanagermodel

        self.slot_setup_page = None
        self.test_manager_page = None

        self.__setup()

    def __run_command(self, command):
        result, msg = self.handler.run_command(command)
        return result, msg

    def __setup(self):
        self.__init_visuals()
        self.__connect_signals()

    def __init_visuals(self):
        self.set_title("Funky Tester")
        self.set_icon_name("applications-testing")
        self.set_resizable = True

        try:
            window_width = self.get_screen().get_width()
            window_height = self.get_screen().get_height()
        except AttributeError:
            logging.info("Please set DISPLAY variable before running this Funky Tester.")
            sys.exit(1)

        if window_width >= ftw.MAX_WIN_WIDTH:
            window_width = ftw.MAX_WIN_WIDTH
            window_height = ftw.MAX_WIN_HEIGHT
        self.set_size_request(window_width, window_height)

        # create main vbox
        self.vbox = gtk.VBox(False, 0)
        self.vbox.set_border_width(0)
        self.add(self.vbox)

        # create notebook
        self.notebook = gtk.Notebook()
        self.notebook.set_tab_pos(gtk.POS_LEFT)

        # create pages 
        self.slot_setup_page = PlatformSlotSetupPage(self)
        self.test_manager_page = TestManagerPage(self)
        
        # create statusbar 
        self.statusbar = gtk.Statusbar()
        
        # add them to notebook
        self.notebook.insert_page(self.slot_setup_page,  
                gtk.Label("Slot Setup"),     self.SLOT_SETUP)
        self.notebook.insert_page(self.test_manager_page,  
                gtk.Label("Test Manager"),  self.TEST_MANAGER)

        # add it all to the vbox
        self.vbox.pack_start(self.notebook, expand=True, fill=True)
        self.vbox.pack_start(self.statusbar, expand=False, fill=False)
        self.set_property('window-position', gtk.WIN_POS_CENTER)

        self.notebook.set_current_page(0)

    def __connect_signals(self):
        self.connect("destroy", lambda *w: gtk.main_quit())
        self.handler.connect('platform-init', self.__setup_platform_cb)
        self.handler.connect('platform-ready', self.__platform_ready_cb)
        self.handler.connect('platformslot-ready', self.__platformslot_ready_cb)
        self.handler.connect('platformslot-init', self.__platformslot_init_cb)
        self.handler.connect('uut-ready', self.__uut_ready_cb)
        self.handler.connect('uut-init', self.__uut_init_cb)
        self.handler.connect('update-status', self.__update_statusbar_cb)
        self.handler.connect('error', self.__error_cb)

    def __terminate(self):
        self.handler.running = False
        self.__run_command("TERMINATE")
        gtk.main_quit()

    def __display_error(self, message=None, event=None):
        if event:
            message = "Address: {0} \n{1}".format(event.address,
                    event.traceback)
        error = gtk.MessageDialog(self, 
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                gtk.MESSAGE_WARNING,
                gtk.BUTTONS_NONE,
                message)
        error.set_property('window-position', gtk.WIN_POS_CENTER)
        error.set_transient_for(self)
        error.show()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # Callbacks
    #

    def __error_cb(self, handler, event):
        if event.traceback:
            self.__display_error(event=event)
        elif event.message:
            self.__display_error(event.message)
    
    def __update_statusbar_cb(self, handler, event):
        message = event.message
        self.context_id = self.statusbar.get_context_id("update-event")
        self.statusbar.push(self.context_id, message)

    def __uut_ready_cb(self, handler, event):
        pass

    def __uut_init_cb(self, handler, event):
        uut = UnitUnderTestAdapter(
                handler = self.handler,
                address = event.address,
                status = event.status,
                product_type = None,
                name = event.name,
                )
        logging.debug(uut)
        self.testmanagermodel.add(uut)

    def __platformslot_ready_cb(self, handler, event):
        pass

    def __platformslot_init_cb(self, handler, event):
        platformslot = PlatformSlotAdapter(
                handler = self.handler,
                address = event.address,
                status = event.status,
                current_uut = None,
                product_type = None,
                name = event.name,
                )
        manifest, msg = self.__run_command( ("get_manifest", RecipientType.SLOT,
            platformslot.address, "", True) )
        self.slotsmanagermodel.add(platformslot)
        self.slot_setup_page.add_slot(platformslot, ("Product", manifest),
            self.__get_product_version_cb,
            is_ready_cb=self.__configure_platformslot_cb)

    def __platform_ready_cb(self, event):
        self.show_all()

    def __setup_platform_cb(self, handler, event):
        result, msg = self.__run_command(
                ("is_setup", RecipientType.PLATFORM, None, "", True) )
        if not result:
            manifest, msg = self.__run_command(
                    ("get_manifest", RecipientType.PLATFORM, None, "", True) )
            dialog = AbstractSelectionDialog(
                    "Please select the test platform.",
                    "Test Platform Selection",
                    self,
                    ("Platform", manifest),
                    self.__get_platform_versions_cb)
            dialog.connect('response', self.__dialog_response_cb,
                    self.__configure_platform_cb)
            dialog.show()

    def __configure_platformslot_cb(self, ready, adapter):
        if ready:
            result, msg = self.__run_command( ("configure", RecipientType.SLOT,
                adapter.address, "", False) )

    def __configure_platform_cb(self):
        result, msg = self.__run_command(
                ("configure", RecipientType.PLATFORM, None, "", False) )

    def __dialog_response_cb(self, dialog, response_id,
            accept_callback=None):
        if ( response_id == gtk.RESPONSE_DELETE_EVENT or 
                response_id == gtk.RESPONSE_REJECT ):
            dialog.destroy()
            self.__terminate()
        if response_id == gtk.RESPONSE_ACCEPT:
            dialog.destroy()
            if callable(accept_callback):
                self.show_all()
                accept_callback()

    def __get_product_version_cb(self, name, adapter):
        version_list, message = self.__run_command(
                ("select_product", RecipientType.SLOT, adapter.address, name, True) )
        return ("Version", version_list), self.__set_product_version_cb

    def __set_product_version_cb(self, name, adapter):
        spec_list, message = self.__run_command(
                ("set_product_version", RecipientType.SLOT, adapter.address, name,
                    True) )
        return ("Specification", spec_list), self.__set_product_specification_cb

    def __set_product_specification_cb(self, name, adapter):
        result = self.__run_command(
                ("set_product_specification", RecipientType.SLOT,
                    adapter.address, name, False) )
        return None

    def __get_platform_versions_cb(self, name, adapter):
        version_list, message = self.__run_command(
                ("select_platform", RecipientType.PLATFORM, None, name, True) )
        return ("Version", version_list), self.__set_platform_version_cb

    def __set_platform_version_cb(self, name, adapter):
        result = self.__run_command(
                ("set_platform_version", RecipientType.PLATFORM, None, name,
                    True) )
        return None

