#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import threading, time, logging

import gtk, gobject

import ft.event

from ui.elements.functeventhandler import FuncTEventHandler
from ui.elements.functester import FunctionalTestWindow
from ui.elements.models.testmodels import TestManagerModel
from ui.elements.models.slotsmodels import SlotsManagerModel

def main(server_connection):
    gtk.gdk.threads_init()

    #-------------------
    # Instantiate models to be shared between user interface and event handler
    #
    testmanagermodel = TestManagerModel()
    slotsmanagermodel = SlotsManagerModel()

    #-------------------
    # Configure event handler, set up event handling thread, start main GUI loop
    #
    functhandler = FuncTEventHandler(server_connection, 
            testmanagermodel, slotsmanagermodel)
    functwindow = FunctionalTestWindow(functhandler)
    
    functhandler.start()
    gtk.main()

if __name__ == "__main__":
    try:
        ret = main()
    except Exception:
        ret = 1
        import traceback
        traceback.print_exc(20)
        
    sys.exit(ret)
