#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import Queue as StdLibQueue, threading, logging, os, socket
from multiprocessing import Queue

import ft.event
from ft.platform import Platform

class PlatformServerConnection(threading.Thread):

    def __init__(self):
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
            if messsage:
                self.__handle_message(message)
            self.__handle_outgoing_queue()

class PlatformSocketServer(threading.Thread):

    def __init__(self, address, port):
        super(PlatformSocketServer, self).__init__()

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((address, port))

        self.running = False

        self.commands = None
        self.platform = None # is set externally
        self.outgoing_queue = Queue()
        self.event_registry = PlatformEventHandlerRegistry()

    def fire(self, event, **kwargs):
        e = event(**kwargs)
        self.outgoing_queue.put(e)
    
    def __run_command(self, command):
        return self.commands.run_command(command)

    def run(self):
        self.running = True
        self.commands = self.platform.commands
        self.main()

    def main(self):
        while self.running:
            command = self.__receive_command()
            self.__handle_command(command)
            self.__handle_outgoing_queue()
        self.__cleanup()

    def __receive_command(self):
        pass

    def __handle_command(self, command):
        pass

    def __get_event(self):
        pass

    def __handle_outgoing_queue(self):
        event = self.__get_event()
        if event:
            self.

    def __cleanup()
        pass

class PlatformEventhandlerRegistry(object):
    pass

class PlatformServer(object):

    def init_server(self, address=None, port=None):

        self.server = PlatformSocketServer(address, port)
        self.serverinfo = (self.server.address, self.server.port)

    def init_platform(self):
        pass

    def detach(self):
        pass

    def establish_connection(self):
        pass

    def launch_ui(self):
        pass

    def terminate(self):
        pass
