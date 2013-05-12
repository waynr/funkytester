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
        self.title_height = 24
        self.row_height = 18

    def _add(self, parent_iter, adapter):
        row_iter = self.append( parent_iter, ( adapter.status,
            adapter.current_uut, adapter.product_type ))
        self.__set_tv_height()
        return row_iter

    def __set_tv_height(self):
        count = 0
        rowiter = iter(self)
        for row in rowiter:
            count += 1
        self.set_treeview_size(-1, self.title_height + self.row_height * count)
    ## Function gets set externally otherwise does nothing. Use grep.
    #
    def set_treeview_size(treeview,):
        pass

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
