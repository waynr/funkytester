#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import gtk

def create_labeled_hbox(markup = "Nonce", widget = None, *args):
    hbox = gtk.HBox(*args)
    hbox.label = gtk.Label()
    hbox.label.set_markup(markup)
    hbox.pack_start(hbox.label)
    if widget:
        hbox.pack_start(widget)
    return hbox
