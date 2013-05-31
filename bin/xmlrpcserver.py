#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

from optparse import OptionParser
import inspect
import sys

from os import path

bindir = path.dirname(__file__)
topdir = path.dirname(bindir)
libdir = path.join(topdir, "lib")
extdir = path.join(topdir, "ext")

sys.path.insert(0, libdir)
sys.path.insert(0, extdir)

import logging
logging.basicConfig(
    #filename    = "gf_info.txt",
    Stream      = sys.stdout,
    format      = "%(levelname)-5s %(module)-5s %(funcName)-5s %(message)s",
    level       = logging.DEBUG )

from SimpleXMLRPCServer import (
        SimpleXMLRPCServer,
        SimpleXMLRPCRequestHandler,
        )

from interfaces.xmlrpc import (
        EMACXMLRPCInterface,
        ServerInterface,
        )
from ft.device import emac_devices

def main():
    parser          = OptionParser()
    parser.add_option("-p", "--port", action="store", type="int", dest="port")
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose")
    parser.add_option("-q", "--quiet", action="store_false", dest="verbose")
    
    parser.set_defaults(
            port=8000,
            verbose=False,
            )
    
    (options, args) = parser.parse_args()
    ip_address      = args[0]      
    port            = options.port      
    verbose         = options.verbose      
    
    #-------------------------------------------------------------------------------
    # dynamically import required modules and append imported names to a list
    #
    
    interface_names = []
    interfaces      = []
    module          = sys.modules[__name__]
    
    for name, obj in inspect.getmembers(emac_devices):
        if inspect.isclass(obj):
            interface_names.append(name)
            interfaces.append(obj)
    
    temp    = __import__('ft.device.emac_devices', globals(), locals(), interface_names,
            -1)
    
    for name, obj in inspect.getmembers(temp):
        if inspect.isclass(obj):
            setattr(module, name, obj)
    
    #-------------------------------------------------------------------------------
    # define xmlrpc request handler
    # 
    
    class RequestHandler(SimpleXMLRPCRequestHandler):
        rpc_paths   = ("/RPC2",)
    
    #-------------------------------------------------------------------------------
    # something something ip address? not sure what this is supposed to do...
    # 
    
    #ip      = BinaryCall(
            #kwargs={ 
                #"binary_full_path"  : "ip", 
                #"instance_name"     : "macaddr", 
                #}
            #)
    
    #-------------------------------------------------------------------------------
    # start server, register functions from dynamically imported module list
    #
    
    server  = SimpleXMLRPCServer(
            (ip_address, port),
            requestHandler  = RequestHandler,
            allow_none  = True,
            )
        
    server.register_instance( EMACXMLRPCInterface(interface_list=interfaces) )
    #server.register_introspection_functions()
    
    #-------------------------------------------------------------------------------
    # run server until killed by signal
    #
    
    server.serve_forever()

if __name__ == "__main__":
    main()
