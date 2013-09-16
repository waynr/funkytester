#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import logging, time

## Mixin class to provide common event implementor functionality.
# 
#  Events items encapsulate various pieces of information about the Platform
#  object that inherits from the "EventGenerator" class. This allows remote
#  "shadow" representations of Platform objects to be updated asynchronously
#  from within Platform code.
#
class EventGenerator(object):

    def fire(self, event, **kwargs):
        self.event_handler.fire(event, **kwargs)

    ## Updates client representation with important information about the
    #  represented Platform object.
    #
    #  @param on_mask Bitmask containing status bits that need to be set.
    #  @param off_mask Bitmask containing status bits that need to be unset.
    #  @param kwargs All other key word arguments passed to the method are
    #  passed on to the 'fire' method.
    #
    def fire_status(self, on_mask=None, off_mask=None, **kwargs):
        if on_mask:
            self.status |= on_mask
        if off_mask:
            self.status &= ~off_mask

        self.fire(TestEvent,
                obj = self,
                status = self.status,
                datetime = time.time(),
                **kwargs
                )

## Base class for events
#
#  All events must be serializeable (no passing python objects to constructors).
#  This is necessary to ensure that a smooth transition can be made between
#  a local-only architecture to a client-server architecture in which one client
#  UI might potentially control many servers.
#
#  Since events will be fired by objects which most likely has a corresponding
#  representation in the UI, we need a way for the UI to associate an event with
#  objects in a one-to-many manner (each underlying object may be represented
#  multiple times in the UI). To facilitate this, a the concept of object
#  "address" will be used so that the UI can the state of and send commands to
#  these objects. This address will be stored in a tuple which hierarchically
#  denotes the object being represented. Below are the initial format
#  specifications for these tuples for different objects:
#
#  Platform
#    Format (xmlrpc): ("<ip_address>:<port>",)
#
#    Platforms will only be addressable when the Network-based PlatformServer
#    (probably XMLRPC-based) has been written. For the multiprocessing-based
#    implementation, it will always be represented by "None".
#    
#  Platform Slot
#    Format: (<platform_address>, <index>,)
#
#  Unit Under Test
#    Format: (<platform_address>, <serial_number>,)
#
#  Specification
#    Format: There is no anticipated need to represent the Specification object
#    during event handling at this time.
#
#  Test
#    Format 1: (<platformslot_address>, <test_name>,)
#    Format 2: (<platformslot_address>, <test_index>,)
#
#  Action
#    Format 1: (<test_address>, <action_name>,)
#    Format 2: (<test_address>, <action_index>,)
#
class Event(object):

    ## Event Constructor.
    #  
    #  @param obj The object referred to by this event.
    #
    #  @param kwargs All the keyword arguments passed to this event.
    #
    def __init__(self, obj=None, **kwargs):
        if obj and hasattr(obj, "address"):
            self.address = obj.address
        for key, value in kwargs.items():
            setattr(self, key, value)
        del obj

    def get_all(self):
        return self.__dict__

#-------------------------------------------------------------------------------
# Event Base Classes

## Base class for test events.
#
class TestEvent(Event):
    """ Test Event """ 

## Base class for action events.
#
class ActionEvent(Event):
    """ Action Event """

## Base class for specification events.
#
class SpecificationEvent(Event):
    """ Specification Event """

## Base class for platform events.
#
class PlatformEvent(Event):
    """ Platform Event """

## Base class for platform slot events.
#
class PlatformSlotEvent(Event):
    """ Platform Slot Event """

## Base class for unit under test events.
#
class UnitUnderTestEvent(Event):
    """ Unit Under Test Event """

## Base class for errors that occur on the backend.
#
class ErrorEvent(Event):
    """ Error Event """

## Event class indicates that object has been destroyed.
#
class DestroyEvent(Event):
    """ Destroy Event """

#-------------------------------------------------------------------------------
# Misc Events

class UpdateStatus(Event):
    """ Test Ready """

#-------------------------------------------------------------------------------
# Test Events

## Event indicates test instance is ready to run.
#
class TestReady(TestEvent):
    """ Test Ready """

## Event indicates test instance has been initialized.
#
class TestInit(TestEvent):
    """ Test Init """

## Event indicates test instance has begun running.
#
class TestStart(TestEvent):
    """ Test Start """

## Event indicates running test instance has encountered a fatal error.
#
class TestFatal(TestEvent):
    """ Test Fatal """

## Event indicates running test instance has finished.
#
class TestFinish(TestEvent):
    """ Test Finish """

## Event indicates that the given test's data has been logged.
#
class TestLogged(TestEvent):
    """ Test Logged """

## Event that tells the UI to pop up an Interactive test dialog.
#
class TestInteract(TestEvent):
    """ Test Interact """

#-------------------------------------------------------------------------------
# Action Events

## Event indicates action instance has been initialized.
#
class ActionInit(ActionEvent):
    """ Action Init """

## Event indicates action instance is ready to run.
#
class ActionReady(ActionEvent):
    """ Action Ready """

## Event indicates action instance has begun running.
#
class ActionStart(ActionEvent):
    """ Action Start """

## Event indicates running action instance has finished.
#
class ActionFinish(ActionEvent):
    """ Action Finish """

## Event indicates action instance has been initialized.
#
class ActionFatal(ActionEvent):
    """ Action Fatal """

#-------------------------------------------------------------------------------
# Platform Events

## Event indicates that platform object exists and is ready to be set up.
#
class PlatformInit(PlatformEvent):
    """ Platform Init """

## Event indicates that platform has been set up and is ready.
#
class PlatformReady(PlatformEvent):
    """ Platform Ready """

## Event indicates that platform has changed or is about to change.
#
class PlatformChange(PlatformEvent):
    """ Platform Change """

#-------------------------------------------------------------------------------
# Platform Slot Events

## Event indicates that platform slot object has been initialized.
#
class PlatformSlotInit(PlatformSlotEvent):
    """ Platform Slot Ready """

## Event indicates that platform slot is ready for a new UUT.
#
class PlatformSlotReady(PlatformSlotEvent):
    """ Platform Slot Ready """

## Event indicates that platform slot is currently busy with a UUT.
#
class PlatformSlotBusy(PlatformSlotEvent):
    """ Platform Slot Busy """

#-------------------------------------------------------------------------------
# UnitUnderTest Events

## Event indicates that UUT is ready to begin.
#
class UUTInit(UnitUnderTestEvent):
    """ UUT Ready """

## Event indicates that UUT is ready to begin.
#
class UUTReady(UnitUnderTestEvent):
    """ UUT Ready """

## Event indicates that UUT is busy.
#
class UUTBusy(UnitUnderTestEvent):
    """ UUT Busy """

## Event indicates that UUT is currently loading bootloader.
#
class UUTProgramBootloader(UUTBusy):
    """ UUT Program Bootloader """

## Event indicates that UUT is currently running nfs test.
#
class UUTRunNFSTest(UUTBusy):
    """ UUT Run NFS Test """

## Event indicates that UUT is currently loading kernel/fs.
#
class UUTLoadKFS(UUTBusy):
    """ UUT Load KFS """

## Event indicates that UUT is currently first-booting.
#
class UUTFirstBoot(UUTBusy):
    """ UUT First Boot """

