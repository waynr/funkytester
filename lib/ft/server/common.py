#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

from multiprocessing import Queue
import time, threading, logging, Queue as StdLibQueue

class PlatformClient(threading.Thread):

    def __init__(self):
        super(PlatformClient, self).__init__(name="PlatformClient")

        self.handler_registry = EventHandlerRegistry()

        self.outgoing_queue = Queue()
        self.incoming_queue = Queue()

        self.running = threading.Event()
        self.setDaemon = True

    def run(self):
        self.running.set()
        self.main()

    def main(self):
        while self.running.is_set():
            message = self._receive_message()
            if message:
                self._handle_message(message)
            self._handle_outgoing_queue()

    def run_command(self, command):
        self.outgoing_queue.put(command)
        if command == "TERMINATE":
            while not self.outgoing_queue.empty():
                time.sleep(0.5)
            return None, ""
        try:
            response = self.incoming_queue.get(True, 20)
            if response:
                return response
        except StdLibQueue.Empty:
                raise PlatformTimeoutError ("FATAL: Timeout while awaiting "
                        "response from PlatformServer.")
        except KeyboardInterrupt:
            pass

    def register_handler(self, handler):
        self.handler_registry.register_handler(handler)

    def terminate(self):
        self.run_command("TERMINATE")
        while not self.outgoing_queue.empty():
            pass
        self._terminate()

    def _terminate(self):
        pass

## Generic event handler registry; register event handlers here. For the sake of
#  this discussion, an "event handler" is any object that has a "fire" method
#  which takes a single non-self argument.
#
class EventHandlerRegistry(object):

    def __init__(self):
        self._temp_queue = Queue()
        self.handlers = list()

    def fire(self, event):
        if len(self.handlers) == 0:
            self._temp_queue.append(event)
            return

        for handler in self.handlers:
            handler.notify(event)

    def register_handler(self, handler):
        self.handlers.append(handler)
        return True

    def unregister_handler(self, handler):
        if handler in self.handlers:
            self.handlers.remove(handler)
            return True
        return False

## Error indicates timeout occurred between client and server.
#
class PlatformTimeoutError(Exception):
    # Indiciates timeout occurred between client and server.
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)
