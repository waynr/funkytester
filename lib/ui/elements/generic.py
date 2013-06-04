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

import sys

import gtk, gobject

class FunctTreeStore(gtk.TreeStore):

    def __init__(self, *args):
        super(FunctTreeStore, self).__init__(*args)
        if not self.columns:
            self.columns = []
        if not self.valid_adapter_types:
            self.valid_adapter_types = []
        self._init_visuals()

    def add(self, adapter):
        check = self._check_adapter(adapter)
        if not check:
            return False

        # check if adapter is already in this testmodel
        if adapter.get_iter("testmodel"):
            return True

        parent_iter = None
        if adapter.parent_address:
            parent_address = adapter.parent_address
            parent = GenericAdapter.get(address = parent_address)
            parent_iter = parent.get_iter("testmodel")

        row_iter = self._add(parent_iter, adapter)
        adapter.set_iter("testmodel", row_iter)

        return True

    def _add(self, parent_iter, adapter):
        raise NotImplementedError

    def _check_adapter(self, adapter):
        for adapter_type in self.valid_adapter_types:
            if isinstance(adapter, adapter_type):
                return True
        return False

    def _init_visuals(self):
        self.tvcolumns = [None] * len(self.columns)
        
        for n in range(0, len(self.columns)):
            self.tvcolumns[n] = gtk.TreeViewColumn(self.columns[n][0], None)

            if len(self.columns[n][1]) == 0:
                cell = gtk.CellRendererText()
                self.tvcolumns[n].pack_start(cell) # XXX might need expand=False
                text_column = self.columns[n][2]
                self.tvcolumns[n].set_attributes(cell, text=text_column)
            else:
                for i, func in enumerate(self.columns[n][1]):
                    cell = gtk.CellRendererText()
                    self.tvcolumns[n].pack_start(cell) # XXX might need expand=False
    
                    text_column = self.columns[n][2]
                    if text_column:
                        self.tvcolumns[n].set_attributes(cell, text=text_column)
                    if not func == None:
                        self.tvcolumns[n].set_cell_data_func(cell, func, n)

class GenericAdapter(gobject.GObject):

    __gsignals__ = {
            'on-changed'    : (gobject.SIGNAL_RUN_LAST,
                                gobject.TYPE_NONE,
                                ()), 
            }

    ## Maintains a dictionary to access instances by address.
    #
    __registry = dict()

    def __setattr__(self, name, value):
        super(GenericAdapter, self).__setattr__(name, value)
        if not name.startswith("_"):
            self.emit('on-changed')

    def __init__(self, handler=None, **kwargs):
        super(GenericAdapter, self).__init__()
        self.name = None
        self.status = None
        self.datetime = None
        self.additional_info = None
        self.address = None
        self.parent_address = None

        self.handler = handler

        self.__iters = {}

        self.__update(kwargs)
        self.__registry[self.address] = self

    def update(self, event):
        event_attrs = event.get_all()
        self.__update(event_attrs)

    def __update(self, kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def run_command(self, command):
        # The future is commented out.
        #self.handler.run_command(self.address, self.recipient_type, command)

        # For now, stick to established convention. There will be time in the
        # future to fix this.
        return self.handler.run_command( (command[0], self.recipient_type,
                self.address, command[1], command[2]) )

    @staticmethod
    def get(address=None): 
        if GenericAdapter.__registry.has_key(address):
            return GenericAdapter.__registry[address]
        return None
    
    def get_iter(self, context):
        if self.__iters.has_key(context):
            return self.__iters[context] 
        return None

    def set_iter(self, context, itr):
        self.__iters[context] = itr

