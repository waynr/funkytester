#!/usr/bin/env python

# standard libs
import copy, xmlrpclib, sys, logging
from functools import wraps

##
# @brief Check to see if there is an XML RPC client interface available to
# connect to a remote instance of the interface in question
#

def xmlrpc_call(f):
    
    @wraps(f)
    def wrapper(self, kwargs):
        if self._is_local():
            result  = f(self, kwargs=kwargs)
        else:
            # get instance name
            instance_name   = self.instance_name
            method_name     = f.__name__
            xmlrpc_client   = self.xmlrpc_client
            result          = xmlrpc_client.call_method(
                    instance_name, 
                    method_name, 
                    kwargs,
                    )
        return result

    return wrapper

##
# @brief Apply xmlrpc_call to all of a class's methods that do not begin with an
# underscore.
#

def xmlrpc_all(cls):
    for method_name, method in cls.__dict__.items():
        if (method_name.startswith("_") or not callable(method)): 
            continue
        setattr(cls, method_name, xmlrpc_call(method))

    return cls

@xmlrpc_all
class ServerInterface(object):
    def __init__(self, instance_name=None, xmlrpc_client=None, kwargs={}):
        self.xmlrpc_client  = xmlrpc_client
        self.instance_name  = instance_name

        if not self._is_local():
            xmlrpc_client.create_instance(
                    instance_name, 
                    self.__class__.__name__, 
                    kwargs,
                    )

    def _is_local(self,):
        if isinstance(self.xmlrpc_client, xmlrpclib.ServerProxy):
            return False
        else:
            return True

## Provide an interface to tests using a XMLRPC Server
class EMACXMLRPCInterface(object):
    def __init__(self, interface_list=None):
        self.interfaces = dict()
        self.instances  = dict()

        if interface_list == None:
            raise ValueError("Must pass a list of tests!")

        self.__create_interface_dict(interface_list)

    def __create_interface_dict(self, interface_list):
        for interface in interface_list:
            self.__add_interface(interface)

    def __add_interface(self, interface):
        name = interface.__name__
        logging.debug(name)
        if not self.interfaces.has_key(name):
            self.interfaces[name] = interface

    def create_instance(self, instance_name, interface_name, kwargs):
        if self.instances.has_key(instance_name):
            return False
        self.instances[instance_name] = self.interfaces[interface_name](kwargs)

    def get_interfaces(self):
        return self.interfaces.keys()

    def get_instances(self):
        return self.instances.keys()

    def call_method(self, instance_name, method_name, kwargs):
        instance    = self.instances[instance_name]

        logging.debug("Call method: {0} from: {1}".format(method_name, instance_name))
        method      = getattr(instance, method_name)
        result      = method(kwargs=kwargs)

        return result

