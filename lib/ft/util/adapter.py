#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

## package adapter
#  This package provides an adapter that causes a backend object to notify all
#  of its associated UI objects when some change has been made.
#

from functools import wraps

def setattr_update_ui(self, name, value):
    object.__setattr__(self, name, value)
    if not self.__dict__.has_key("ui_elements"):
        self.__dict__["ui_elements"] = list()
    for ui_element in self.ui_elements:
        update = getattr(ui_element, "update", False)
        if update:
            update()
        else:
            raise Exception("No update() attribute found for %s!" 
                    % ui_element)

def ui_adapter(cls):
    setattr(cls, "__setattr__", setattr_update_ui)
    return cls
