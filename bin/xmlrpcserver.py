#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

from optparse import OptionParser
from os import path
import inspect, sys, logging, pdb

bindir = path.dirname(__file__)
topdir = path.dirname(bindir)
libdir = path.join(topdir, "lib")
extdir = path.join(topdir, "ext")

sys.path.insert(0, libdir)
sys.path.insert(0, extdir)

log_file = path.join(topdir, "xmlrpcserver.log")

logging.basicConfig(
    level = logging.DEBUG,
    format = "%(asctime)s %(name)-5s %(levelname)-5s %(module)-5s " + \
            "%(funcName)-5s %(message)s",
            datefmt = '%Y%m%d %H:%M:%S',
    filename = log_file,
    filemode = 'a',
    )

from SimpleXMLRPCServer import (
        SimpleXMLRPCServer,
        SimpleXMLRPCRequestHandler,
        )

from interfaces.xmlrpc import (
        EMACXMLRPCInterface,
        ServerInterface,
        )

from ft.device import emac_devices

def parse_options():
    parser = OptionParser()
    parser.add_option("-p", "--port", action="store", type="int", dest="port")
    parser.add_option("-P", "--pydebug", action="store_false", dest="pydebug")
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose")
    parser.add_option("-q", "--quiet", action="store_false", dest="verbose")
    
    parser.set_defaults(
            port=8000,
            verbose=False,
            )
    return parser.parse_args()
    
def main():
    (options, args) = parse_options()

    ip_address = args[0]      
    port = options.port      
    verbose = options.verbose      
    
    #-------------------------------------------------------------------------------
    # dynamically import required modules and append imported names to a list
    #
    
    interface_names = []
    interfaces = []
    module = sys.modules[__name__]
    
    for name, obj in inspect.getmembers(emac_devices):
        if inspect.isclass(obj):
            interface_names.append(name)
            interfaces.append(obj)
    
    temp = __import__('ft.device.emac_devices', globals(), locals(), interface_names,
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
    # start server, register functions from dynamically imported module list
    #
    
    server  = SimpleXMLRPCServer(
            (ip_address, port),
            requestHandler  = RequestHandler,
            allow_none  = True,
            )
        
    server.register_instance( EMACXMLRPCInterface(interface_list=interfaces) )
    
    #-------------------------------------------------------------------------------
    # run server until killed by signal
    #
    
    if options.pydebug:
        pdb.set_trace()
    server.serve_forever()

if __name__ == "__main__":
    main()
