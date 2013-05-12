#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import gtk

from ui.elements import adapters
from ui.elements.generic import FunctTreeStore

class TestManagerModel(FunctTreeStore):

    (UUT,
     TEST,
     ACTION) = range(3)

    def __init__(self):
        self.columns = [
                ("Name/ID", [None]),
                ("Status", [None]),
                ("DateTime", [None]),
                ("Additional Info", [self.__additional_info_data]),
                ]
        self.valid_adapter_types = [
                adapters.unit.UnitUnderTestAdapter,
                adapters.test.TestAdapter,
                adapters.action.ActionAdapter,
                ]
        super(TestManagerModel, self).__init__(str, str, str, str)

    def _add(self, parent_iter, adapter):
        row_iter = self.append( parent_iter, ( adapter.name, adapter.status,
            adapter.datetime, adapter.additional_info ))

    def __additional_info_data(self, treeview_column, cell, model, iter, 
            user_data):
        obj = model.get_value(iter, n)
        cell.set_property('text', str(obj))
        return

