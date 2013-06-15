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

    model_type = "test"

    def __init__(self):
        self.columns = [
                ("Name/ID", 
                    {'text':0},
                    {'xalign':0.0, 'width-chars':20}),
                ("Status", 
                    {'text':1, 'cell_background':5},
                    {'xalign':0.5, 'width-chars':25}),
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

        path = self.get_path(row_iter)
        row = self[path]

        handler_ids = []
        hid = adapter.connect('on-changed', self.__update, row)
        handler_ids.append(hid)

        hid = adapter.connect('destroy', self.__remove_row_cb, row)
        handler_ids.append(hid)

        return row, handler_ids

    def __remove_row_cb(self, adapter=None, row=None):
        if not row:
            return None

        if not adapter:
            adapter = row[4]

        handler_ids = adapter.get_handler_ids(self.model_type)
        for hid in handler_ids:
            adapter.disconnect(hid)
            adapter.del_handler_id(self.model_type, hid)

        adapter.del_row(self.model_type)
        self.remove(row.iter)

    def __update(self, adapter, row):
        status_message, status_bg_color = self.__dispatch_data_function(
                "_status", adapter)

        if adapter.datetime:
            dt = datetime.datetime.fromtimestamp(adapter.datetime)
            date_time = dt.strftime("%m/%d/%y, %I:%M:%S %p")
        else:
            date_time = "N/A"

        self[row.iter] = (adapter.name, status_message, date_time,
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

        message = ""
        gdk_color = '#FFFFFF'

        while True:
            if status & UnitUnderTest.State.INIT:
                message += "INIT"
                break

            if not status & UnitUnderTest.State.ACTIVE:
                gdk_color = "#FF5555"
                message += "Inactive"
                break
            elif not status & UnitUnderTest.State.POWER:
                message += "Power Off"
                break

            if status & UnitUnderTest.State.LINUX:
                if status & UnitUnderTest.State.BOOT_NFS:
                    message += "NFS"

                if status & UnitUnderTest.State.BOOT_FLASH:
                    message += "FLASH"

                message += "Linux | "
                if status & UnitUnderTest.State.LOAD_TESTS:
                    message += "Loading Tests"
                    break
                if status & UnitUnderTest.State.TESTING:
                    message += "Testing"
                    break
                if status & UnitUnderTest.State.READY:
                    message += "Ready"
                else:
                    message += "Busy"
                break
    
            if status & UnitUnderTest.State.BOOTING:
                message += "Booting"
                break

            if status & UnitUnderTest.State.BOOTL:
                message += "U-Boot | "
                if status & UnitUnderTest.State.READY:
                    message += "Ready"
                else:
                    message += "Busy"
                break

            message += "Unknown"
            break

        return message, gtk.gdk.Color(gdk_color)
        
    def _status_test_cb(self, adapter):
        status = adapter.status

        message = status
        gdk_color = '#FFFFFF'

        if status & Test.State.RUNNING:
            gdk_color = '#0033FF'
            message = "Running"
        elif status & Test.State.HAS_RUN:
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

        if status & Action.State.RUNNING:
            gdk_color = '#0033FF'
            message = "Running"
        elif status & Action.State.HAS_RUN:
            if status & Action.State.FAIL:
                gdk_color = '#FF0033'
                message = "Fail"
            else:
                gdk_color = '#00FF33'
                message = "Pass"
        elif status == Action.State.INIT:
            message = "INIT"

        return message, gtk.gdk.Color(gdk_color)
        
