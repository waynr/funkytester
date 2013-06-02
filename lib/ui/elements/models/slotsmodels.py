#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import gtk, gobject

from ui.elements import adapters
from ui.elements.generic import FunctTreeStore

from ft.platform import PlatformSlot

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
        super(SlotsManagerModel, self).__init__(str, str, str, gobject.TYPE_PYOBJECT)

    def _add(self, parent_iter, adapter):
        row_iter = self.append( parent_iter, ( adapter.status,
            adapter.current_uut, adapter.product_type, adapter))
        adapter.connect('on-changed', self.__update, row_iter)
        return row_iter

    def __update(self, adapter, row_iter):
        product_data = "{0} | {1} | {2}".format(adapter.product_type,
                adapter.metadata_version, adapter.specification_name)
        self[row_iter] = (adapter.status, adapter.current_uut,
                product_data, adapter)

    def __status_data(self, treeview_column, cell, model, iter, 
            user_data):
        status = int(model.get_value(iter, 0), 16)
        cell.set_property('xalign', 0.5)
        cell.set_property('width-chars', 15)

        if status & PlatformSlot.State.POWER:
            message = "Power On"
            cell.set_property('cell-background', gtk.gdk.Color('#00FF33'))
        elif status & PlatformSlot.State.OCCUPIED:
            message = "Slot Occupied"
            cell.set_property('cell-background', gtk.gdk.Color('#FFBF00'))
        else:
            message = "Slot Empty"
            cell.set_property('cell-background', gtk.gdk.Color('#FFFFFF'))

        cell.set_property('text', message)
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

