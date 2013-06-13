#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import logging, datetime

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
                ("Name/ID", 
                    {'text':0},
                    {'xalign':0.0, 'width-chars':15}),
                ("Status", 
                    {'text':1, 'cell_background':5},
                    {'xalign':0.5, 'width-chars':15}),
                ("DateTime", 
                    {'text':2},
                    {'xalign':0.5, 'width-chars':21}),
                ("Additional Info", 
                    {'text':3},
                    {'xalign':0.0,} ),
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

    def _add(self, parent_iter, adapter):
        status_message, status_bg_color = self.__dispatch_data_function(
                "_status", adapter)
        row_iter = self.append(parent_iter, (adapter.name, status_message,
            adapter.datetime, adapter.additional_info, adapter,
            status_bg_color))
        adapter.connect('on-changed', self.__update, row_iter)
        return row_iter

    def __update(self, adapter, row_iter):
        status_message, status_bg_color = self.__dispatch_data_function(
                "_status", adapter)

        if adapter.datetime:
            dt = datetime.datetime.fromtimestamp(adapter.datetime)
            date_time = dt.strftime("%m/%d/%y, %I:%M:%S %p")
        else:
            date_time = "N/A"

        self[row_iter] = (adapter.name, status_message, date_time,
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

        message = status
        gdk_color = '#FFFFFF'

        if status & UnitUnderTest.State.POWER:
            message = "Power On"

        if status == UnitUnderTest.State.INIT:
            message = "INIT"

        return message, gtk.gdk.Color(gdk_color)
        
    def _status_test_cb(self, adapter):
        status = adapter.status

        message = status
        gdk_color = '#FFFFFF'

        if status & Test.State.HAS_RUN:
            if status & Test.State.FAIL:
                gdk_color = '#FF0033'
                message = "Fail"
            else:
                gdk_color = '#00FF33'
                message = "Pass"

        if not status & Test.State.VALID:
            message = "Invalid Test"
            gdk_color = '#202020'

        if status == Test.State.VALID:
            message = "INIT"

        return message, gtk.gdk.Color(gdk_color)

    def _status_action_cb(self, adapter):
        status = adapter.status

        message = status
        gdk_color = '#FFFFFF'

        if status & Action.State.HAS_RUN:
            if status & Action.State.FAIL:
                gdk_color = '#FF0033'
                message = "Fail"
            else:
                gdk_color = '#00FF33'
                message = "Pass"

        if status == Action.State.INIT:
            message = "INIT"

        return message, gtk.gdk.Color(gdk_color)
        
