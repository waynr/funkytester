#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import gtk

from ui.elements.pages.functpage import FunctPage
from ui.elements.functwidgets import (PlatformSlotSetupWidget,
        AbstractSelectionWidget)

class PlatformSlotSetupPage(FunctPage):

    def __init__(self, functester):
        super(PlatformSlotSetupPage, self).__init__(functester, 
                "Platform Slot Setup")
        self.platform_slot_widgets = {}
        self.platform_slot_button_group = []

        self.platform_slot_list = []
        self.show()

    def clear_platform_slots(self):
        pass

    def add_slot(self, platform_slot_adapter, *args, **kwargs):
        product_selection_widget = AbstractSelectionWidget(*args,
                adapter=platform_slot_adapter, **kwargs)
        widget = PlatformSlotSetupWidget(platform_slot_adapter,
                product_selection_widget)
        
        self.pack_start(widget, expand=False, fill=False)
        widget.show()
        #self._update_slot_position(widget)

    def _update_slot_position(self, widget):
        position = self.child_get_property(widget, "position")
        #widget.set_label_by_index(position)
        self.platform_slot_widgets[platform_slot] = (widget, position)


