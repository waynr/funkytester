#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import sys, time, logging, pprint

from sqlalchemy import Column, Integer, String, Boolean, Date, Text, ForeignKey
from sqlalchemy.orm import relationship
from ft import Base

from ft.event import EventGenerator
import ft.event
from ft.util import ui_adapter

## Base class for actions that comprise a test run.
#
class ActionDB(Base):

    __tablename__ = "pyft_action_results"
    id = Column(Integer, primary_key=True)
    name = Column(String(20))
    status = Column(String(20))
    output = Column(Text)
    value = {
            "expected": Column(String(50)),
            "actual": Column(String(50)),
            "tolerance": Column(String(50)), 
            }
    testresult_id = Column(Integer, ForeignKey('pyft_test_results.id'))

    ## Gives a string representation of the Action
    #
    # Prints name and status of the action
    #
    # @param self The object pointer
    #
    def __repr__(self,):
        rstring = "<Action('%s','%s')>" 
        rtuple = self.name, self.status, 
        return rstring % rtuple

    class State:
        INIT        = 0x001
        RUNNING     = 0x002
        HAS_RUN     = 0x004

        FAIL        = 0x100
        BROKEN      = 0x200

## Base class for actions that comprise a test run.
#
class Action(ActionDB, EventGenerator):

    ## The constructor
    #
    # Fires ActionInit and ActionReady events
    #
    # @param self The object pointer
    # @param action_dict The dictionary of actions from a test specification
    #
    def __init__(self, action_dict, parent=None):
        self.test = parent
        self.event_handler = parent.event_handler

        self.name = action_dict["name"]
        self.method_name = action_dict["method_name"]
        self.kwargs = action_dict["kwargs"]
        self.action_class = action_dict["class"]
        self.is_remote = action_dict["remote"]
        self.constructor_args = action_dict["constructor_args"]

        self.allow_fail = False
        self.kwargs_value_key = "value"
        self.log_output = True

        if action_dict.has_key("allow_fail"):
            self.allow_fail = action_dict["allow_fail"]

        if action_dict.has_key("kwargs_value_key"):
            self.kwargs_value_key = action_dict["kwargs_value_key"]

        if action_dict.has_key("log_output"):
            log_action_output   = action_dict["log_output"]

        self.status = Action.State.INIT

        self.instances = {}

    def destroy(self):
        self._destroy()
        self.fire( ft.event.DestroyEvent,
                obj = self,
                )
    
    def _destroy(self):
        # finish database operations?
        # decrease reference count on remote xmlrpc objects?
        pass

    def set_address(self, address):
        self.address = (self.test.address, address)
        self.fire( ft.event.ActionInit,
                obj = self,
                name = self.name,
                status = self.status,
                )

    ## Generates an instance of the class specified by the test action
    # 
    def _generate_instance(self,):
        instances       = self.instances

        name            = self.name
        constructorargs = self.constructor_args
        constructorargs["instance_name"]    = name

        instances[name] = self.action_class(kwargs=constructorargs)

    ## Clears action instances
    # 
    @staticmethod
    def clear_instances():
        Action.instances = dict()

    ## Calls the action, fires events to signal that the action begins and ends
    #
    # Fires the ActionStart event. After testing, a TestFinish event is fired.
    #
    # @param self The object pointer
    # @param value Value of the keyword arguments, defaulted to None
    #
    def call(self, value=None):
        self.fire(ft.event.ActionStart,
                obj = self
                )
        self.fire_status(Action.State.RUNNING | Action.State.FAIL)
        if not value == None:
            self.kwargs[self.kwargs_value_key] = value
        try:
            result = self._call()
        except:
            import traceback
            msg = traceback.format_exc()
            logging.debug(msg)
            self.fire(ft.event.ErrorEvent,
                    obj = self,
                    traceback = msg
                    )
            result = None
        else:
            self.fire_status(None, Action.State.FAIL) 
            self.fire(ft.event.ActionFinish,
                obj = self
                )
        self.fire_status(Action.State.HAS_RUN, Action.State.RUNNING)
        return result

    def _call(self,):
        instances = self.instances

        if not instances.has_key(self.name):
            self._generate_instance()

        instance = instances[self.name]
        method = getattr(instance, self.method_name)
        output = method(self.kwargs)

        if not output == None:
            self.exit_status, self.output = output

        logging.debug(self.name)
        logging.debug(output)
        return output
    
    def set_status(self, exp='', act='', tol=''):
        self.value= {
                "expected": exp,
                "actual": act,
                "tolerance": tol,
                }
        self.fire_status(value = self.value)

if __name__ == "__main__":
    a   = Action()

