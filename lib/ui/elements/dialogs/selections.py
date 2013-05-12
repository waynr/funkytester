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

import sys, os.path as path

import gtk

from ui.elements.functwidgets import AbstractSelectionWidget

class AbstractSelectionDialog(gtk.Dialog):

    def __init__(self, instructions="None", title="Selection Window",
            parent=None, *args):
        super(AbstractSelectionDialog, self).__init__(title, parent,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                (   gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, 
                    gtk.STOCK_OK, gtk.RESPONSE_ACCEPT ) )
        self.selection_widget = AbstractSelectionWidget(
                is_ready_cb=self.__set_okaybutton_sensitive,
                *args)
        self.__init_visuals(instructions)

    def __set_okaybutton_sensitive(self, sensitive, adapter=None):
        buttons = self.action_area.get_children()
        buttons[0].set_sensitive(sensitive)

    def __init_visuals(self, instructions):
        if instructions:
            label = gtk.Label(instructions)
            self.vbox.pack_start(label)
            label.show()

        self.vbox.set_spacing(10)
        self.vbox.pack_start(self.selection_widget)
        self.selection_widget.show()

        self.set_property('window-position', gtk.WIN_POS_CENTER)
        self.__set_okaybutton_sensitive(False)
