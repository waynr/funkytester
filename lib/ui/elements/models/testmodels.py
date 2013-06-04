#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import logging

import gtk, gobject

from ui.elements import adapters
from ui.elements.generic import FunctTreeStore
from ui.elements.adapters import (
        UnitUnderTestAdapter,
        TestAdapter,
        ActionAdapter,
        )

from ft.platform import UnitUnderTest
from ft.test import Test, Action

class TestManagerModel(FunctTreeStore):

    (UUT,
     TEST,
     ACTION) = range(3)

    def __init__(self):
        self.columns = [
                ("Name/ID", [None], 0),
                ("Status", [None], 1),
                ("DateTime", [None], 2),
                ("Additional Info", [None], 3),
                ]
        self.valid_adapter_types = [
                adapters.unit.UnitUnderTestAdapter,
                adapters.test.TestAdapter,
                adapters.action.ActionAdapter,
                ]
        super(TestManagerModel, self).__init__(
                str, str, str, str,  # name, status, datetime, additional_info
                gobject.TYPE_PYOBJECT, # adapter object
                str, # status background color string
                )

        status_cr_list = self.tvcolumns[1].get_cell_renderers()
        status_cr = status_cr_list[0] 
        self.tvcolumns[1].set_attributes(status_cr, cell_background=5)

    def _add(self, parent_iter, adapter):
        logging.debug(adapter.name)
        row_iter = self.append( parent_iter, ( adapter.name, adapter.status,
            adapter.datetime, adapter.additional_info, adapter, gtk.gdk.Color('#FFFFFF')))
        adapter.connect('on-changed', self.__update, row_iter)
        return row_iter

    def __update(self, adapter, row_iter):
        logging.debug(adapter.name)
        status_message, status_bg_color = self.__dispatch_data_function(
                "_status", adapter)
        self[row_iter] = (adapter.name, status_message, adapter.datetime,
                adapter.additional_info, adapter, status_bg_color)

    def __dispatch_data_function(self, method_name, adapter, *args, **kwargs):
        if isinstance(adapter, UnitUnderTestAdapter):
            suffix = "_uut_cb"
        elif isinstance(adapter, TestAdapter):
            suffix = "_test_cb"
        elif isinstance(adapter, ActionAdapter):
            suffix = "_action_cb"
        else:
            raise TypeError("Invalid Adapter: {0}".format(adapter))

        method_name += suffix

        if hasattr(self, method_name):
            method = getattr(self, method_name)
            return method(adapter, *args, **kwargs)
        return "nonce", gtk.gdk.Color('#F0F0F0')

    def _status_uut_cb(self, adapter):
        status = adapter.status

        message = "INIT"
        gdk_color = gtk.gdk.Color('#FFFFFF')

        if status & UnitUnderTest.State.POWER:
            message = "powered up"

        return message, gdk_color
        
    def _status_test_cb(self, adapter):
        status = adapter.status

        gdk_color = gtk.gdk.Color('#FFFFFF')
        message = "Not Run"

        if status & Test.State.HAS_RUN:
            if status & Test.State.FAIL:
                gdk_color = gtk.gdk.Color('#FF0kk033')
                message = "Fail"
            else:
                gdk_color = gtk.gdk.Color('#00FF33')
                message = "Pass"

        return message, gdk_color

    def _status_action_cb(self, adapter):
        status = adapter.status

        message = "INIT"
        gdk_color = "#FFFFFF"

        return message, gdk_color
        
