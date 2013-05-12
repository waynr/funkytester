#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

from ui.elements.generic import GenericAdapter

from ft.command import RecipientType

class UnitUnderTestAdapter(GenericAdapter):

    def __init__(self, **kwargs):
        super(UnitUnderTestAdapter, self).__init__(**kwargs)
        self.recipient_type = RecipientType.UUT
