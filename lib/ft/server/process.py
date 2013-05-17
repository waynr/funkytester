#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import Queue as StdLibQueue
from multiprocessing import Process, Pipe, Queue
import signal, logging, threading, os

import ft.event
from ft.platform import Platform

class PlatformServerConnection(threading.Thread):

    def __init__(self, server_info):
        super(PlatformServerConnection, self).__init__()

        self.channel = server_info[0]
        self.handler_registry = PlatformEventHandlerRegistry()

        self.outgoing_queue = Queue()
        self.incoming_queue = Queue()

        self.running = False
        self.setDaemon = True

    def run(self):
        self.running = True
        self.main()

    def main(self):
        while self.running:
            message = self.__receive_message()
            if message:
                self.__handle_message(message)
            self.__handle_outgoing_queue()

    def __receive_message(self):
        try:
            if self.channel.poll():
                message = self.channel.recv()
                return message
        except Exception:
            return None, "ERROR: Problem receiving command response."

    def __handle_message(self, message):
        if isinstance(message, ft.event.Event):
            logging.debug(message)
            self.handler_registry.fire(message)
        elif message[0] == "RESPONSE":
            self.incoming_queue.put(message[1])
        else:
            logging.error("Unhandled PlatformServer message:" 
                    " {0}".format(message))

    def __get_outgoing_item(self):
        try:
            return self.outgoing_queue.get(False)
        except StdLibQueue.Empty:
            return None

    def __handle_outgoing_queue(self):
        command = self.__get_outgoing_item()
        if command:
            self.channel.send(command)

    def run_command(self, command):
        self.outgoing_queue.put(command)
        if command == "TERMINATE":
            return None, ""
        try:
            response =  self.incoming_queue.get(True, 10)
            if response:
                return response
            else:
                return None, "FATAL: Timeout while waiting for response from PlatformServer."
        except KeyboardInterrupt:
            pass

    def register_handler(self, handler):
        self.handler_registry.register_handler(handler)

    def terminate(self):
        self.run_command("TERMINATE")
        
class PlatformProcessServer(Process):

    def __init__(self, server_channel):
        super(PlatformProcessServer, self).__init__(name="PlatformProcessServer")
        self.daemon = True
        self.channel = server_channel

        self.running = False
        self.commands = None
        self.platform = None # is set externally

        self.outgoing_queue = Queue()
        self.event_registry = PlatformEventHandlerRegistry()

    def run(self):
        self.running = True
        self.commands = self.platform.commands
        self.main()

    def main(self):
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        while self.running:
            command = self.__receive_command()
            self.__handle_command(command)
            self.__handle_outgoing_queue()
        self.__cleanup()

    def fire(self, event, **kwargs):
        e = event(**kwargs)
        self.outgoing_queue.put(e)

    def __handle_outgoing_queue(self):
        event = self.__get_event()
        if event:
            self.channel.send(event)

    def __get_event(self):
        try:
            return self.outgoing_queue.get(False)
        except StdLibQueue.Empty:
            return None

    def __handle_command(self, command):
        if command == "TERMINATE":
            self.running = False
            return False
        if command == None:
            return False
        logging.debug(command)
        result = ("RESPONSE", self.__run_command(command))
        self.channel.send(result)

    def __run_command(self, command):
        return self.commands.run_command(command)

    def __receive_command(self):
        try:
            if self.channel.poll():
                command = self.channel.recv()
                return command
        except Exception:
            return None, "ERROR: Problem receiving command response."
    
    def __cleanup(self):
        self.channel.close()
        self.platform.cleanup()

## Keep track of event handlers (remote and local) for event distribution.
#
class PlatformEventHandlerRegistry(object):

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

## PlatformServer is an interface wraps some type of server to provide a
#  consistent API during program startup so that different server
#  implementations can be used with relatively little difficulty using the same
#  code.
#
class PlatformServer(object):

    ## Initialize the daemon which will control the platform during testing, and
    #  if applicable to server type set "serverinfo" tuple.
    #
    def init_server(self):
        self.ui_channel, self.server_channel = Pipe()

        self.server = PlatformProcessServer(self.server_channel)
        self.serverinfo = (self.ui_channel, self.server_channel)

    def init_platform(self, manifest_file):
        self.platform = Platform(manifest_file, self.server)
        self.server.platform = self.platform
        return

    ## If running locally as a thread or process, start the thread/process and
    #  return to calling context.
    #
    def detach(self):
        self.server.start()
        return

    ## Initiate and return connection to a remote PlatformServer.
    #
    def establish_connection(self):
        self.connection = PlatformServerConnection(self.serverinfo)
        return self.connection

    ## Launch given UI main() with the given args.
    #
    def launch_ui(self, uifunc, *args):
        return uifunc(*args)

    ## Stop PlatformServer backend.
    #
    def terminate(self):
        self.server.running = False
        self.connection.terminate()
        self.server.join()
