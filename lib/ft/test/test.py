#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import logging, pprint, time, sys, threading

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
    
    class State:
        INIT        = 0x001
        RUNNING     = 0x002
        HAS_RUN     = 0x004
        VALID       = 0x008

        FAIL        = 0x100
        BROKEN      = 0x200
        INVALID_INTERFACE = 0x400

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
    def __new__(cls, test_dict, *args, **kwargs):
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

    def __del__(self):
        self.destroy()

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
        self.uut_id = parent.serial_number
        self.test_dict  = test_dict

        self.lock = threading.RLock()

        self.unit_under_test = parent
        self.event_handler = parent.event_handler

        self.xmlrpc_client = xmlrpc_client

        self.name   = test_dict["name"]
        self.type   = test_dict["type"]
        self.shortdesc  = test_dict["shortdesc"]
        self.refdes = test_dict["refdes"]

        self.max_retry  = 5
        if test_dict.has_key("max_retry"):
            self.max_retry  = test_dict["max_retry"]

        self.status = Test.State.INIT

        if test_dict["valid"]:
            self.status |= Test.State.VALID

    def set_address(self, index):
        self.address = (self.unit_under_test.address, index)
        self.fire( ft.event.TestInit,
                obj = self,
                name = self.name,
                status = self.status,
                )

    def fire(self, event, **kwargs):
        self.event_handler.fire(event, **kwargs)

    def _fire_status(self, state_bit=None, on=True, **kwargs):
        if state_bit:
            if on:
                self.status |= state_bit
            elif not on:
                self.status &= ~state_bit

        self.fire(ft.event.TestEvent,
                obj = self,
                status = self.status,
                datetime = time.time(),
                **kwargs
                )

    ## Checks the status of the test's actions and updates the test's
    # status appropriately.
    #
    # If any action fails, the whole test fails. Also handles the case
    # of a successful action with an invalid interface.
    #
    # @param self The object pointer
    #
    def check(self):
        self._check()
        if not self.status & Test.State.VALID:
            if self.status & Test.State.FAIL:
                self._fire_status(Test.State.FAIL | Test.State.BROKEN)
            else:
                self._fire_status(Test.State.INVALID_INTERFACE)

    def _check(self):
        raise NotImplementedError

    def _check_action(self, action):
        if action.status & Action.State.BROKEN:
            self._fire_status(Test.State.BROKEN | Test.State.FAIL)
            return False
        if action.status & Action.State.FAIL:
            self._fire_status(Test.State.FAIL)
            return False
        self._fire_status(Test.State.FAIL, False)
        return True

    ## Runs the test, fires events to signal that the test begins and ends
    #
    # Fires the TestStart event, runs the test a maximum of max_retry times
    # (or until the test breaks), then checks the status of the test's
    # actions. After testing, a TestFinish event is fired.
    #
    # @param self The object pointer
    #
    def run(self,):
        self.fire(ft.event.TestStart,
                obj = self
                )
        count   = 0
        while count < self.max_retry:
            try:
                self._run()
            except:
                import traceback
                msg = traceback.format_exc()
                logging.debug(msg)
                self.status |= Test.State.BROKEN
                self.fire(ft.event.TestFatal,
                        obj = self
                        )
            else:
                break
            count += 1
            #time.sleep(.1)
        self.check()
        self.fire(ft.event.TestFinish,
                obj = self,
                status = self.status,
                )

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

    def destroy(self):
        self._destroy()
        self.fire( ft.event.DestroyEvent,
                obj = self,
                )

    def _destroy(self):
        raise NotImplementedError

    class CommandsSync:
        @staticmethod
        def acknowledge(uut, data):
            pass

    class CommandsAsync:
        @staticmethod
        def run(test, data):
            test.run()

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
        self.actions    = []
        
    def initialize_actions(self):
        for i, action_dict in enumerate(self.test_dict["actionlist"]):
            set_remote(action_dict, self.xmlrpc_client)
            action = Action(action_dict, self)
            action.set_address(i)
            self.actions.append(action)

    def _check(self):
        for action in self.actions:
            if not self._check_action(action):
                break

    ## Runs the SingleTest
    #
    # Updates status of each action
    #
    # @param self The object pointer
    #
    def _run(self,):
        self._fire_status(Test.State.RUNNING)

        output_list = list()

        for action in self.actions:
            output = action.call()

            if output == None:
                action.status != Action.State.BROKEN
                action.status != Action.State.FAIL
            else:
                exit_status, output = output
                if output == None:
                    output = ""
                if not (exit_status == "0" or exit_status == 0):
                    action.status  |= Action.State.FAIL

            # ugly hack: if allow_fail then make a failure look like a success
            # (for actions such as mounting a drive that might "fail" if the
            # drive is already mounted). This is not included in the preceding
            # logic because it will be easier to remove later if left on its
            # own.

            if action.allow_fail:
                action.status &= ~Action.State.FAIL

            action._fire_status()

        self._fire_status(Test.State.RUNNING, False)
        self._fire_status(Test.State.HAS_RUN)
    
    def _destroy(self):
        for action in self.actions[::-1]:
            action.destroy()

## Test class
#
# Creates and runs an ExpectTest. ExpectTests check a list of actions by keeping
# track of changes in state in the platform and then verifying that the expected
# states are recieved by the UUT.
#
class ExpectTest(Test,):

    ## The constructor
    #
    # Sets up two lists of dictionaries to keep track of state changes in the
    # test's actions.
    #
    # @param self The object pointer
    # @param xmlrpc_client Connection to the UUT to facilitate the transparent
    # proxy
    # @param uut_id Serial number of the UUT
    # @param test_dict Dictionary from the test
    #
    def __init__(self, *args, **kwargs):
        super(ExpectTest, self).__init__(*args, **kwargs)

    def initialize_actions(self):
        test_dict = self.test_dict

        self.statechangers  = list( dict() )
        self.statecheckers  = list( dict() )

        for i, action_dict in enumerate(test_dict["statechangers"]):
            set_remote(action_dict, self.xmlrpc_client)
            action = Action(action_dict, self)
            action.set_address(i)
            self.statechangers.append( 
                    { 
                        "action" : action, 
                        "values" : action_dict["values"], 
                        }
                    )
        
        action_dict = test_dict["statechecker"]
        set_remote(action_dict, self.xmlrpc_client)

        action = Action(action_dict, self)
        action.set_address(None)

        self.statecheckers.append( {
                    "action" : action,
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

    def _check(self):
        for action in self.statecheckers:
            if not self._check_action(action["action"]):
                break

    ## Runs the ExpectTest
    #
    # Runs the statechanger actions, then the statechecker. The test succeeds
    # if the actual value matches the expected value up to some tolerance.
    # Each action's status is updated accordingly.
    #
    # @param self The object pointer
    #
    def _run(self,):
        self._fire_status(Test.State.RUNNING)

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
                    action.status &= ~Action.State.FAIL
                else:
                    action.status |= Action.State.FAIL
                    logging.debug(pprint.pformat( {
                        "name"       : action.name,
                        "tolerance"         : tolerance,
                        "expected_value"    : expected_value,
                        "test_value"        : test_value,
                        } ) )
    
                action.set_status(expected_value, test_value, tolerance)

        self._fire_status(Test.State.RUNNING, False)
        self._fire_status(Test.State.HAS_RUN)
    
    def _destroy(self):
        for action in self.statecheckers[::-1]:
            action["action"].destroy()
            self.statecheckers.remove(action)

        for action in self.statechangers[::-1]:
            action["action"].destroy()
            self.statechangers.remove(action)

## Test class
#
# Creates and runs an InteractTest. InteractTests are loose wrappers around the
# Test base class which allow the test platform to query the user when a
# particular piece of functionality cannot be automatically verified.
#
class InteractTest(Test):

    ## The constructor
    #
    # @param self The object pointer
    # @param uut_id Serial number of the UUT
    # @param test_dict Dictionary from the test
    #
    def __init__(self, *args, **kwargs):
        super(InteractTest, self).__init__(*args, **kwargs)
        test_dict = self.test_dict
        if test_dict["valid"]:
            self.status |= Test.State.VALID

    def initialize_actions(self):
        pass # does nothing; _run instead requests information from UI

    ## Stub implementation.
    #
    def _check(self):
        pass

    ## Runs the ExpectTest
    #
    # Fires an InteractTest event 
    #
    def _run(self):
        self._fire_status(Test.State.RUNNING)
        self.fire( ft.event.TestInteract,
                obj = self,
                prompt = self.test_dict["message"],
                pass_text = self.test_dict["responses"]["pass"],
                fail_text = self.test_dict["responses"]["fail"],
                )

    def _destroy(self):
        pass

    class CommandsAsync(Test.CommandsAsync):
        @staticmethod
        def set_pass(test, data):
            test._fire_status(Test.State.HAS_RUN)
            test._fire_status(Test.State.RUNNING | Test.State.FAIL |
                    Test.State.BROKEN | Test.State.INVALID_INTERFACE, False)

        @staticmethod
        def set_fail(test, data):
            test._fire_status(Test.State.HAS_RUN | Test.State.FAIL)
            test._fire_status(Test.State.RUNNING, False)

