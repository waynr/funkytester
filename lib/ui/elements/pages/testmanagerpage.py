#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import gtk

from ui.elements.pages.functpage import FunctPage

class TestManagerPage(FunctPage):

    def __init__(self, functester,):
        super(TestManagerPage, self).__init__(functester, 
                "Platform Control")
        self.functest = functester

        self.testmanagermodel = functester.testmanagermodel
        self.slotsmanagermodel = functester.slotsmanagermodel

        self.init_visuals()

    def init_visuals(self):
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

        self.slotsmanagermodel.set_treeview_size = (
                self.treeview_slots.set_size_request )
        self.treeview_slots.set_size_request(-1, 100)
        #self.treeview_slots.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color('#335533'))
        #self.treeview_slots.modify_bg(gtk.STATE_INSENSITIVE, gtk.gdk.Color('#335533'))

        self.treeview_tests = gtk.TreeView(self.testmanagermodel)
        for column in self.testmanagermodel.tvcolumns:
            self.treeview_tests.append_column(column)

        self.scrolledwindow_tests = gtk.ScrolledWindow()
        self.scrolledwindow_tests.add(self.treeview_tests)

        self.box["right"].pack_start(self.treeview_slots, False, False, 10)
        self.box["right"].pack_start(self.scrolledwindow_tests)

        self.pack_start(self.box["main"])
