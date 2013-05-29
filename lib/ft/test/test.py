#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import logging
import pprint
import time
import sys

from functools import wraps

from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from ft import Base

import ft.event
from ft.test import Action
from ft.util import ui_adapter

class TestDB(Base):
    
    __tablename__ = "pyft_test_results"
    id = Column(Integer, primary_key=True)
    name = Column(String(20))
    status = Column(String(20))
    refdes = Column(String(100))
    output = Column(Text)

    uut_id = Column(Integer, ForeignKey('pyft_unit_under_test.id'))
    actions = relationship("Action")

    ## Gives a string representation of the Test
    #
    # Prints name, status of the test, and reference designater
    #
    # @param self The object pointer
    #
    def __repr__(self,):
        rstring = "<Test('%s','%s','%s')>" 
        rtuple = self.name, self.status, self.refdes
        return rstring % rtuple
    
    class Status:
        INIT = "Initialized"
        SUCCESS = "Success"
        FAIL = "Fail"
        BROKEN = "Broken Test"

## Test class to provide common functionality among a broad category of test
# types. Also acts as an abstract interface to specify functionality required of
# sub classes.
#
class Test(TestDB):

    ## Creates a new Test object
    #
    # Ensures that the test is either SingleTest or ExpectTest; Raises 
    # TypeError if not. Returns the loaded test.
    #
    # @param cls The Test
    # @param xmlrpc_client Connection to the UUT to facilitate the transparent proxy
    # @param uut_id Serial number of the UUT
    # @param test_dict Dictionary 
    #
    def __new__(cls, test_dict, parent):
        if cls is Test:
            test_type = test_dict["type"]
            if test_type == "single":
                test = super(Test, cls).__new__(SingleTest)
            elif test_type == "expect":
                test = super(Test, cls).__new__(ExpectTest)
            elif test_type == "interact":
                test = super(Test, cls).__new__(InteractTest)
            else:
                raise TypeError("Invalid test type: {0}".format(test_type))

            return test
        else:
            return super(Test, cls).__new__(cls)

    ## The constructor
    #
    # Automatically sets max_retry to 5 if none is specified
    #
    # @param self The object pointer
    # @param xmlrpc_client Connection to the UUT to facilitate the transparent proxy
    # @param uut_id Serial number of the UUT
    # @param test_dict Dictionary 
    #
    def __init__(self, test_dict, parent, xmlrpc_client=None):
        self.uut_id = parent.serial_num
        self.parent = parent
        self.test_dict  = test_dict

        self.name   = test_dict["name"]
        self.type   = test_dict["type"]
        self.shortdesc  = test_dict["shortdesc"]
        self.refdes = test_dict["refdes"]
        self.is_valid   = test_dict["valid"]

        self.max_retry  = 5
        if test_dict.has_key("max_retry"):
            self.max_retry  = test_dict["max_retry"]

        self.debug["count"] = self.debug["count"] + 1

        self.status = Status.init
        logging.debug(pprint.pformat(self.debug))

    def set_address(self, index):
        self.address = (self.parent.address, index)
        self.set_status(Test.Status.INIT)
        ft.event.fire( ft.event.TestInit,
                obj = self,
                status = self.status,
                )

    def fire(self, event, **kwargs):
        self.parent.fire(event, **kwargs)

    ## Runs the test, fires events to signal that the test begins and ends
    #
    # Fires the TestStart event, runs the test a maximum of max_retry times
    # (or until the test breaks), then checks the status of the test's
    # actions. After testing, a TestFinish event is fired.
    #
    # @param self The object pointer
    #
    def run(self,):
        ft.event.fire(ft.event.TestStart(self))
        count   = 0
        while count < self.max_retry:
            try:
                self._run()
            except:
                self.status = Status.broken_test
                ft.event.fire(ft.event.TestFatal(self))
            count += 1
            time.sleep(.1)
        self.status = self.check_actions()
        ft.event.fire(ft.event.TestFinish(self))

    ## Checks the status of the test's actions and updates the test's
    # status appropriately.
    #
    # If any action fails, the whole test fails. Also handles the case
    # of a successful action with an invalid interface.
    #
    # @param self The object pointer
    #
    def check_actions(self,):
        for action in self.actions:
            if action.status == Status.fail:
                self.status = Status.fail
                break
        if not self.is_valid:
            if self.status == Status.success:
                self.status = Status.success_invalid_interface
            else:
                self.status = Status.success

    ## Runs the test
    #
    # Raises a NotImplementedError, indicating that the child Test class (either
    # SingleTest or ExpectTest) has not implemented _run code specific to its 
    # type of test.
    #
    # @param self The object pointer
    #
    def _run(self,):
        raise NotImplementedError

    ## Retrieves a given attribute if it exists
    #
    # If the attribute does not exist, an AttributeError exception is raised
    #
    # @param self The object pointer
    # @param attr The attribute sought (as a string)
    #
    def get(self, attr):
        return getattr(self, attr)

## Method that adds xmlrpc_client object to the action_dict provided
#
# @param action_dict A dictionary of actions from the test
# @param xmlrpc_client Connection to the UUT to facilitate the transparent proxy
#
def set_remote(action_dict, xmlrpc_client):
    if action_dict["remote"]:
        action_dict["constructor_args"]["xmlrpc_client"] \
                = xmlrpc_client

## Test class
#
# Creates and runs a SingleTest. A SingleTest checks actions by running them and 
# detecting if they succeed or fail.
#
class SingleTest(Test,):

    ## The constructor
    #
    # Initializes the test, fires TestInit and TestReady events
    #
    # @param self The object pointer
    # @param xmlrpc_client Connection to the UUT to facilitate the transparent proxy
    # @param uut_id Serial number of the UUT
    # @param test_dict Dictionary from the test
    #
    def __init__(self, *args, **kwargs):
        super(SingleTest, self).__init__(*args, **kwargs)
        ft.event.fire(ft.event.TestInit(self))

        self.actions    = []
        
        for action_dict in self.test_dict["actionlist"]:
            set_remote(action_dict, xmlrpc_client)
            self.actions.append( Action(action_dict, self) )

        ft.event.fire(ft.event.TestReady(self))
    
    ## Runs the SingleTest
    #
    # Updates status of each action
    #
    # @param self The object pointer
    #
    def _run(self,):
        output_list = list()

        for action in self.actions:
            action.status = Status.success

            output = action.call()

            if not output == None:
                exit_status, output = output

            if output == None:
                output = ""

            if not (exit_status == "0" or exit_status == 0):
                action.status  = Status.fail

            # ugly hack: if allow_fail then make a failure look like a success
            # (for actions such as mounting a drive that might "fail" if the
            # drive is already mounted). This is not included in the preceding
            # logic because it will be easier to remove later if left on its
            # own.

            if action.allow_fail:
                action.status = Status.success

## Test class
#
# Creates and runs an ExpectTest. ExpectTests check a list of actions by keeping
# track of changes in state in the platform and then verifying that the expected states
# are recieved by the UUT.
#
class ExpectTest(Test,):

    ## The constructor
    #
    # Sets up two lists of dictionaries to keep track of state changes in the test's
    # actions.
    #
    # @param self The object pointer
    # @param xmlrpc_client Connection to the UUT to facilitate the transparent proxy
    # @param uut_id Serial number of the UUT
    # @param test_dict Dictionary from the test
    #
    def __init__(self, *args, **kwargs):
        super(ExpectTest, self).__init__(*args, **kwargs)
        test_dict = self.test_dict

        self.statechangers  = list( dict() )
        self.statecheckers  = list( dict() )

        for action_dict in test_dict["statechangers"]:
            set_remote(action_dict, xmlrpc_client)
            self.statechangers.append( 
                    { 
                        "action" : Action(action_dict, self), 
                        "values" : action_dict["values"], 
                        }
                    )
        
        action_dict = test_dict["statechecker"]

        set_remote(action_dict, self.xmlrpc_client)

        self.statecheckers.append( {
                    "action" : Action(action_dict, self), 
                    "values" : action_dict["values"],
                    } )

        self.timeout    = 0
        if test_dict.has_key("timeout"):
            self.timeout    = test_dict["timeout"]

        self.tolerance  = 0
        if test_dict.has_key("tolerance"):
            self.tolerance  = test_dict["tolerance"]

        num_values = None

        for statechecker in self.statecheckers:
            if num_values == None:
                num_values = len(statechecker["values"])

            if not num_values == len(statechecker["values"]):
                raise exception("mismatch between number of values and number" \
                        " of expected values. please revise the test spec")

            num_values = len(statechecker["values"])

        for statechanger in self.statechangers:
            if not num_values == len(statechanger["values"]):
                raise exception("mismatch between number of values and number" \
                        " of expected values. please revise the test spec")

            num_values = len(statechanger["values"])

        self.num_values = num_values

    ## Runs the ExpectTest
    #
    # Runs the statechanger actions, then the statechecker. The test succeeds
    # if the actual value matches the expected value up to some tolerance.
    # Each action's status is updated accordingly.
    #
    # @param self The object pointer
    #
    def _run(self,):
        for i in range(self.num_values):
            # run statechanger actions
            for statechanger in self.statechangers:
                action = statechanger["action"]
                action.call(statechanger["values"][i])

            if self.timeout > 0:
                time.sleep(self.timeout)
        
            # run statechecker 
            for statechecker in self.statecheckers:
                action = statechecker["action"]
                output = action.call()

                test_value, exit_status = output

                # check the value obtained against the expected value
                expected_value = statechecker["values"][i]
                
                tolerance = self.tolerance
                if tolerance > 0:
                    max_expected_value  = expected_value + tolerance
                    min_expected_value  = expected_value - tolerance

                if ((tolerance > 0 and
                    ( test_value < max_expected_value and
                        test_value > min_expected_value )) or
                    ( test_value == expected_value )): 
                    action.status = Status.success
                else:
                    action.status = Status.fail
                    logging.debug(pprint.pformat( {
                        "name"       : action.name,
                        "tolerance"         : tolerance,
                        "expected_value"    : expected_value,
                        "test_value"        : test_value,
                        } ) )
    
                action.set_status(tmp_result, expected_value, test_value, 
                        tolerance)

## Test class
#
# Creates and runs an InteractTest. InteractTests are loose wrappers around the
# Test base class which allow the test platform to query the user when a
# particular piece of functionality cannot be automatically verified.
#
class InteractTest(Test,):

    ## The constructor
    #
    # @param self The object pointer
    # @param uut_id Serial number of the UUT
    # @param test_dict Dictionary from the test
    #
    def __init__(self, *args, **kwargs):
        super(InteractTest, self).__init__(*args, **kwargs)
        test_dict = self.test_dict

    ## Runs the ExpectTest
    #
    # Fires an InteractTest event 
    #
    def _run(self):
        pass

