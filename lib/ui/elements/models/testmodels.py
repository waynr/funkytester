#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

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
                ("Name/ID", [self.__name_data]),
                ("Status", [self.__status_data]),
                ("DateTime", [self.__datetime_data]),
                ("Additional Info", [self.__additional_info_data]),
                ]
        self.valid_adapter_types = [
                adapters.unit.UnitUnderTestAdapter,
                adapters.test.TestAdapter,
                adapters.action.ActionAdapter,
                ]
        super(TestManagerModel, self).__init__(str, str, str, str,
                gobject.TYPE_PYOBJECT)

    def _add(self, parent_iter, adapter):
        row_iter = self.append( parent_iter, ( adapter.name, adapter.status,
            adapter.datetime, adapter.additional_info, adapter ))
        adapter.connect('on-changed', self.__update, row_iter)
        return row_iter

    def __update(self, adapter, row_iter):
        self[row_iter] = (adapter.name, adapter.status, adapter.datetime,
                adapter.additional_info, adapter)

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
            method(*args, **kwargs)
            return True
        return False

    ## Format the name column to give useful information to tester.
    #
    def __name_data(self, treeview_column, cell, model, iter, 
            user_data):
        obj = model.get_value(iter, 0)
        cell.set_property('text', obj)

    ## Dispatch a call to an adapter type specific data formatter.
    #
    def __status_data(self, treeview_column, cell, model, iter, 
            user_data):
        adapter = model.get_value(iter, 4)
        if self.__dispatch_data_function("_status_data", adapter,
                treeview_column, cell, model, iter, user_data):
            return

        obj = model.get_value(iter, 1)
        cell.set_property('text', obj)

    def _status_data_uut_cb(self, treeview_column, cell, model, iter, 
            user_data):
        status = int(model.get_value(iter, 1), 16)
        status_message = "nonsense"

        if status & UnitUnderTest.State.POWER:
            status_message = "powered up"

        cell.set_property('text', status_message)
        
    def _status_data_test_cb(self, treeview_column, cell, model, iter, 
            user_data):
        status = int(model.get_value(iter, 1), 16)

        if status & Test.State.HAS_RUN:
            print(status)
            if status & Test.State.FAIL:
                cell.set_property('cell-background', gtk.gdk.Color('#FF0kk033'))
                status_message = "Fail"
            else:
                cell.set_property('cell-background', gtk.gdk.Color('#00FF33'))
                status_message = "Pass"
        else:
            cell.set_property('cell-background', gtk.gdk.Color('#FFFFFF'))
            status_message = "Not Run"

        cell.set_property('text', status_message)

    def _status_data_action_cb(self, treeview_column, cell, model, iter, 
            user_data):
        status = int(model.get_value(iter, 1), 16)
        cell.set_property('text', status)
        
    ## Format the datetime column to give useful information to tester.
    #
    def __datetime_data(self, treeview_column, cell, model, iter, 
            user_data):
        obj = model.get_value(iter, 2)
        cell.set_property('text', obj)

    ## Dispatch a call to an adapter type specific data formatter.
    #
    def __additional_info_data(self, treeview_column, cell, model, iter, 
            user_data):
        adapter = model.get_value(iter, 4)
        if self.__dispatch_data_function("__additional_info_data", adapter,
                treeview_column, cell, model, iter, user_data):
            return

        obj = model.get_value(iter, 3)
        cell.set_property('text', str(obj))

