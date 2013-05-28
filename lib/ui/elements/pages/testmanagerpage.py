#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import gtk, logging

from ui.elements.pages.functpage import FunctPage
from ui.elements.menus.testmanager import (
        UUTManagerMenu, 
        TestManagerMenu, 
        ActionManagerMenu,
        )
from ui.elements.adapters import (
        UnitUnderTestAdapter,
        TestAdapter,
        ActionAdapter,
        )

class TestManagerPage(FunctPage):

    def __init__(self, functester,):
        super(TestManagerPage, self).__init__(functester, 
                "Platform Control")
        self.functest = functester

        self.testmanagermodel = functester.testmanagermodel
        self.slotsmanagermodel = functester.slotsmanagermodel

        self.__init_visuals()
        self.__connect_signals()

    def __init_visuals(self):
        self.box = {}
        self.button = {}

        # - - - - - - - - - - - - - - -
        # create Frame and Box structure
        #
        self.box["main"] = gtk.HBox(False, 0)
        self.box["left"] = gtk.VBox(False, 0)
        self.box["right"] = gtk.VBox(False, 0)

        self.box["main"].pack_start(self.box["left"], False, False, 10)
        self.box["main"].pack_start(gtk.VSeparator(), False, False, 5)
        self.box["main"].pack_start(self.box["right"])

        self.box["right_innerbottom"] = gtk.HBox(False, 0)

        self.box["manage_slot_buttons"] = gtk.VButtonBox()
        self.box["manage_slot_buttons"].set_layout(gtk.BUTTONBOX_CENTER)
        self.box["manage_tests_buttons"] = gtk.VButtonBox()
        self.box["manage_tests_buttons"].set_layout(gtk.BUTTONBOX_CENTER)
        for key in ["manage_slot_buttons", "manage_tests_buttons"]:
            self.box["left"].pack_start(self.box[key])
            self.box[key].set_spacing(10)


        # - - - - - - - - - - - - - - -
        # create buttons
        #
        self.button["add_serial"] = gtk.Button("_Add Serial", None, True)
        for key in ["add_serial"]:
            self.box["manage_slot_buttons"].pack_start(self.button[key])

        self.button["run"] = gtk.Button("_Run", None, True)
        self.button["run_all"] = gtk.Button("Run A_ll", None, True)
        self.button["kill"] = gtk.Button("_Kill", None, True)
        for key in ["run", "run_all", "kill"]:
            self.box["manage_tests_buttons"].pack_start(self.button[key])

        # - - - - - - - - - - - - - - -
        # create treeview controls and vscrollbar
        #
        self.treeview_slots = gtk.TreeView(self.slotsmanagermodel)
        for column in self.slotsmanagermodel.tvcolumns:
            self.treeview_slots.append_column(column)

        self.treeview_tests = gtk.TreeView(self.testmanagermodel)
        for column in self.testmanagermodel.tvcolumns:
            self.treeview_tests.append_column(column)

        self.scrolledwindow_tests = gtk.ScrolledWindow()
        self.scrolledwindow_tests.add(self.treeview_tests)

        self.box["right"].pack_start(self.treeview_slots, False, False, 10)
        self.box["right"].pack_start(self.scrolledwindow_tests)

        self.pack_start(self.box["main"])
        
        # - - - - - - - - - - - - - - -
        # create context menus
        #
        self.uutmanager_menu = UUTManagerMenu()
        self.testmanager_menu = TestManagerMenu()
        self.actionmanager_menu = ActionManagerMenu()

    def __connect_signals(self):
        self.treeview_tests.connect('button-release-event',
                self.__popup_menu_tests_cb )
    
    def __popup_menu_tests_cb(self, treeview, event):
        if event.button == 3:  # right-click
            path, focus_column = treeview.get_cursor()
            model = treeview.get_model()
            row = model[path]
            adapter = row[4]
            self.__dispatch_rightclick_tests(adapter, event.button, event.time)
    
    def __dispatch_rightclick_tests(self, adapter, button, time):
        if isinstance(adapter, UnitUnderTestAdapter):
            logging.debug(adapter)
            self.uutmanager_menu.popup(adapter, button, time)
        elif isinstance(adapter, TestAdapter):
            logging.debug(adapter)
            self.testmanager_menu.popup(adapter, button, time)
        elif isinstance(adapter, ActionAdapter):
            logging.debug(adapter)
            self.actionmanager_menu.popup(adapter, button, time)
        else:
            raise TypeError("Invalid Adapter: {0}".format(adapter))

