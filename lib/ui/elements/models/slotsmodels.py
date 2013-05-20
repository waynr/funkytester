#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import gtk

from ui.elements import adapters

from ui.elements.generic import FunctTreeStore

class SlotsManagerModel(FunctTreeStore):
    
    def __init__(self):
        self.columns = [
                ("Status", [self.__status_data]),
                ("Current Unit Under Test", [self.__currentuut_data]),
                ("Product Type", [self.__producttype_data]),
                ]
        self.valid_adapter_types = [
                adapters.platform.PlatformAdapter,
                adapters.platformslot.PlatformSlotAdapter,
                ]
        super(SlotsManagerModel, self).__init__(str, str, str)

    def _add(self, parent_iter, adapter):
        row_iter = self.append( parent_iter, ( adapter.status,
            adapter.current_uut, adapter.product_type ))
        adapter.connect('on-changed', self.__update, row_iter)
        return row_iter

    def __update(self, adapter, row_iter):
        self[row_iter] = (adapter.status, adapter.current_uut,
                adapter.product_type)

    def __status_data(self, treeview_column, cell, model, iter, 
            user_data):
        obj = model.get_value(iter, 0)
        cell.set_property('text', str(obj))
        cell.set_property('xalign', 0.5)
        cell.set_property('width-chars', 15)
        cell.set_property('cell-background', gtk.gdk.Color('#FF0033'))
        return

    def __currentuut_data(self, treeview_column, cell, model, iter, 
            user_data):
        obj = model.get_value(iter, 1)
        cell.set_property('text', str(obj))
        return

    def __producttype_data(self, treeview_column, cell, model, iter, 
            user_data):
        obj = model.get_value(iter, 2)
        cell.set_property('text', str(obj))
        return
