#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import gtk, gobject

from ui.elements import adapters
from ui.elements.generic import FunctTreeStore
from ui.elements.adapters import PlatformSlotAdapter, PlatformAdapter

from ft.platform import PlatformSlot

class SlotsManagerModel(FunctTreeStore):

    model_type = "slot"
    
    def __init__(self):
        self.columns = [
                ("Status", 
                    {'text':0, 'cell_background':4},
                    {'xalign':0.5, 'width-chars':15}),
                ("Current Unit Under Test", 
                    {'text':1},
                    {'xalign':0.5, 'width-chars':11}),
                ("Product Type", 
                    {'text':2},
                    {'xalign':0.05,}),
                ]
        self.valid_adapter_types = [
                adapters.platform.PlatformAdapter,
                adapters.platformslot.PlatformSlotAdapter,
                ]
        super(SlotsManagerModel, self).__init__(
                str, str, str, # name, status, datetime, additional_info
                gobject.TYPE_PYOBJECT, # adapter object
                str, # status background color string
                )

    def _add(self, parent_iter, adapter):
        status_message, status_bg_color = self.__dispatch_data_function(
                "_status", adapter)
        row_iter = self.append( parent_iter, ( status_message,
            adapter.current_uut, adapter.product_type, adapter,
            status_bg_color))

        path = self.get_path(row_iter)
        row = self[path]

        adapter.connect('on-changed', self.__update, row)
        return row, []

    def __update(self, adapter, row):
        status_message, status_bg_color = self.__dispatch_data_function(
                "_status", adapter)
        product_data = "{0} | {1} | {2}".format(adapter.product_type,
                adapter.metadata_version, adapter.specification_name)
        self[row.iter] = (status_message, adapter.current_uut, product_data,
                adapter, status_bg_color)

    def __dispatch_data_function(self, method_name, adapter, *args, **kwargs):
        if isinstance(adapter, PlatformSlotAdapter):
            suffix = "_platformslot_cb"
        elif isinstance(adapter, PlatformAdapter):
            suffix = "_platform_cb"
        else:
            raise TypeError("Invalid Adapter: {0}".format(adapter))

        method_name += suffix

        if hasattr(self, method_name):
            method = getattr(self, method_name)
            return method(adapter, *args, **kwargs)
        return "nonce", gtk.gdk.Color('#F0F0F0')

    def _status_platformslot_cb(self, adapter):
        status = adapter.status

        if status & PlatformSlot.State.POWER:
            message = "Power On"
            gdk_color = '#00FF33'
        elif status & PlatformSlot.State.OCCUPIED:
            message = "Slot Occupied"
            gdk_color = '#FFBF00'
        else:
            message = "Slot Empty"
            gdk_color = '#FFFFFF'

        return message, gtk.gdk.Color(gdk_color)

