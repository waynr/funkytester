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

import sys

import gtk

class FunctPage(gtk.VBox):
    
    def __init__(self, functester_window, title = None):
        super(FunctPage, self).__init__(False, 0)
        self.functester = functester_window
        self.title = title

        self._init_visuals()
        
    def _init_visuals(self,):
        self.functester_width, self.functester_height = (
                self.functester.size_request() )

        if not self.title:
            self.title = "FuncT -- Functional Test Platform"

        self.title_label = gtk.Label()

        self.box_group_area = gtk.VBox(False, 12)
        self.box_group_area.set_size_request(self.functester_width, 
                self.functester_height)
        self.group_align = gtk.Alignment(xalign = 0, yalign= 0.5, xscale = 1,
                yscale = 1)
        self.group_align.set_padding(15, 15, 73, 73)
        self.group_align.add(self.box_group_area)
        self.box_group_area.set_homogeneous(False)
