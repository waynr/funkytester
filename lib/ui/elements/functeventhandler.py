#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import logging, Queue as StdLibQueue
from multiprocessing import Queue

import gobject

import ft.event

## Implements functional test event handling for the FuncT UI.
#
class FuncTEventHandler(gobject.GObject):

    __gsignals__ = {
            # - - - - - - - - - - - - -
            # test signals
            #
            'test-update'    : (gobject.SIGNAL_RUN_LAST,
                                gobject.TYPE_NONE,
                                (gobject.TYPE_PYOBJECT,)),
            'test-begin'    : (gobject.SIGNAL_RUN_LAST,
                                gobject.TYPE_NONE,
                                ()),
            'test-finish'   : (gobject.SIGNAL_RUN_LAST,
                                gobject.TYPE_NONE,
                                ()),
            'test-ready'    : (gobject.SIGNAL_RUN_LAST,
                                gobject.TYPE_NONE,
                                ()),
            'test-fatal'    : (gobject.SIGNAL_RUN_LAST,
                                gobject.TYPE_NONE,
                                ()),
            'test-init'     : (gobject.SIGNAL_RUN_LAST,
                                gobject.TYPE_NONE,
                                ()),

            # - - - - - - - - - - - - -
            # action signals
            #
            'action-update'    : (gobject.SIGNAL_RUN_LAST,
                                gobject.TYPE_NONE,
                                (gobject.TYPE_PYOBJECT,)),
            'action-start'  : (gobject.SIGNAL_RUN_LAST,
                                gobject.TYPE_NONE,
                                ()),
            'action-finish' : (gobject.SIGNAL_RUN_LAST,
                                gobject.TYPE_NONE,
                                ()),
            'action-init'   : (gobject.SIGNAL_RUN_LAST,
                                gobject.TYPE_NONE,
                                ()),
            'action-ready'  : (gobject.SIGNAL_RUN_LAST,
                                gobject.TYPE_NONE,
                                ()),
            'action-fatal'  : (gobject.SIGNAL_RUN_LAST,
                                gobject.TYPE_NONE,
                                ()),

            # - - - - - - - - - - - - -
            # platform signals
            #
            'platform-update'    : (gobject.SIGNAL_RUN_LAST,
                                gobject.TYPE_NONE,
                                (gobject.TYPE_PYOBJECT,)),
            'platform-init'    : (gobject.SIGNAL_RUN_LAST,
                                gobject.TYPE_NONE,
                                (gobject.TYPE_PYOBJECT,)),
            'platform-ready'    : (gobject.SIGNAL_RUN_LAST,
                                gobject.TYPE_NONE,
                                ()),
            'platform-change'   : (gobject.SIGNAL_RUN_LAST,
                                gobject.TYPE_NONE,
                                ()),

            # - - - - - - - - - - - - -
            # platform signals
            #
            'platformslot-update'    : (gobject.SIGNAL_RUN_LAST,
                                gobject.TYPE_NONE,
                                (gobject.TYPE_PYOBJECT,)),
            'platformslot-init'    : (gobject.SIGNAL_RUN_LAST,
                                gobject.TYPE_NONE,
                                (gobject.TYPE_PYOBJECT,)),
            'platformslot-ready'    : (gobject.SIGNAL_RUN_LAST,
                                gobject.TYPE_NONE,
                                ()),
            'platformslot-busy'     : (gobject.SIGNAL_RUN_LAST,
                                gobject.TYPE_NONE,
                                (gobject.TYPE_PYOBJECT,)),

            # - - - - - - - - - - - - -
            # unit under test signals
            #
            'uut-update'    : (gobject.SIGNAL_RUN_LAST,
                                gobject.TYPE_NONE,
                                (gobject.TYPE_PYOBJECT,)),
            'uut-init' : (gobject.SIGNAL_RUN_LAST,
                                gobject.TYPE_NONE,
                                (gobject.TYPE_PYOBJECT,)),
            'uut-ready' : (gobject.SIGNAL_RUN_LAST,
                                gobject.TYPE_NONE,
                                (gobject.TYPE_PYOBJECT,)),
            'uut-program-bootloader' : (gobject.SIGNAL_RUN_LAST,
                                gobject.TYPE_NONE,
                                ()),
            'uut-run-nfs-test'      : (gobject.SIGNAL_RUN_LAST,
                                gobject.TYPE_NONE,
                                ()),
            'uut-load-kfs'          : (gobject.SIGNAL_RUN_LAST,
                                gobject.TYPE_NONE,
                                ()),
            'uut-first-boot'        : (gobject.SIGNAL_RUN_LAST,
                                gobject.TYPE_NONE,
                                ()),

            # - - - - - - - - - - - - -
            # miscellaneous signals
            # 
            'error'        : (gobject.SIGNAL_RUN_LAST,
                                gobject.TYPE_NONE,
                                (gobject.TYPE_PYOBJECT,)),
            'update-status'        : (gobject.SIGNAL_RUN_LAST,
                                gobject.TYPE_NONE,
                                (gobject.TYPE_PYOBJECT,)),
            
            }

    def __init__(self, platform_connection, testmanagermodel, slotsmanagermodel):
        super(FuncTEventHandler, self).__init__()

        self.platform_connection = platform_connection
        self.event_queue = Queue()
        self.platform_connection.register_handler(self)
        self.platform_connection.start()

        self.testmanagermodel = testmanagermodel
        self.slotsmanagermodel = slotsmanagermodel

    def __get_event(self):
        try:
            return self.event_queue.get(False)
        except StdLibQueue.Empty:
            return None

    def __event_handle_loop(self):
        event = self.__get_event()
        if event:
            self.handle_event(event)
        return True

    def start(self,):
        gobject.timeout_add(100, self.__event_handle_loop)

    def notify(self, event):
        self.event_queue.put(event)

    def run_command(self, command):
        return self.platform_connection.run_command(command)

    # - - - - - - - - - - - - - - - - -
    # Event handlers
    #
    @staticmethod
    def handle_startup_events(event):
        pass

    def handle_event(self, event):

        if isinstance(event, ft.event.TestEvent):
            return self.handle_test_event(event)
        elif isinstance(event, ft.event.ActionEvent):
            return self.handle_action_event(event)
        elif isinstance(event, ft.event.SpecificationEvent):
            return self.handle_specification_event(event)
        elif isinstance(event, ft.event.PlatformEvent):
            return self.handle_platform_event(event)
        elif isinstance(event, ft.event.PlatformSlotEvent):
            return self.handle_platform_slot_event(event)
        elif isinstance(event, ft.event.UnitUnderTestEvent):
            return self.handle_platform_uut_event(event)
        elif isinstance(event, ft.event.ErrorEvent):
            self.emit('error', event)
        elif isinstance(event, ft.event.UpdateStatus):
            self.emit('update-status', event)
        else:
            logging.error("Event type not supported: {0}.".format(str(event)))

        return 

    def handle_test_event(self, event):
        if isinstance(event, ft.event.PlatformReady):
            self.emit('action-ready')
        elif isinstance(event, ft.event.PlatformInit):
            self.emit('action-init', event)
        else:
            self.emit('action-update', event)

        return

    def handle_action_event(self, event):
        if isinstance(event, ft.event.PlatformReady):
            self.emit('action-ready')
        elif isinstance(event, ft.event.PlatformInit):
            self.emit('action-init', event)
        else:
            self.emit('action-update', event)

        return

    def handle_specification_event(self, event):
        raise NotImplementedError

    def handle_platform_event(self, event):

        if isinstance(event, ft.event.PlatformReady):
            self.emit('platform-ready')
        elif isinstance(event, ft.event.PlatformInit):
            self.emit('platform-init', event)
        else:
            self.emit('platform-update', event)

        return 

    def handle_platform_slot_event(self, event):
        if isinstance(event, ft.event.PlatformReady):
            self.emit('platformslot-ready' )
        elif isinstance(event, ft.event.PlatformSlotInit):
            self.emit('platformslot-init', event)
        else:
            self.emit('platformslot-update', event)

        return

    def handle_platform_uut_event(self, event):
        if isinstance(event, ft.event.PlatformReady):
            self.emit('uut-ready' )
        elif isinstance(event, ft.event.UUTInit):
            self.emit('uut-init', event)
        else:
            self.emit('uut-update', event)

        return
