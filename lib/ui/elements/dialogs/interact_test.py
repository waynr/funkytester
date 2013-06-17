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

from string import Template

import gtk

class InteractTestDialog(gtk.Dialog):

    def __init__(self, parent, prompt, pass_text="Pass", fail_text="Fail",
            title="Test Interact Dialog"):
        super(InteractTestDialog, self).__init__(title, parent, 
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, 
                ( pass_text, gtk.RESPONSE_YES, 
                  fail_text, gtk.RESPONSE_NO) )
        self.__init_visuals(prompt)

    def __init_visuals(self, prompt):
        label = gtk.Label(prompt)
        self.vbox.pack_start(label)
        label.show()

        self.vbox.set_spacing(10)
        self.set_property('window-position', gtk.WIN_POS_CENTER)

