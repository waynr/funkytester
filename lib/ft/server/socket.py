#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import Queue as StdLibQueue, threading, logging, os, socket, select
from multiprocessing import Queue

import ft.event
from ft.platform import Platform

from ft.server.sockethandler import QueuedSocketHandler

class PlatformSocketClient(threading.Thread):

    def __init__(self, server_info):
        super(PlatformServerConnection, self).__init__()

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
        self.socket_list = set()

        self.poll_lock = threading.RLock()
        self.poll = select.poll()

        self.accept_thread = threading.Thread(target=self.__acceptor)
        self.accept_thread.daemon = True

        self.running = threading.Event()

        self.commands = None
        self.platform = None # is set externally
        self.event_registry = PlatformEventHandlerRegistry()

    def fire(self, event, **kwargs):
        e = event(**kwargs)
        for socket_handler in socket_list:
            socket_handler.put(e)
    
    def __run_command(self, command):
        return self.commands.run_command(command)

    def __acceptor(self):
        while self.running.is_set():
            client_socket, address = self.socket.accept()
            client = QueuedSocketHandler(client_socket, address)
            self.__register_socket(client)

    def run(self):
        self.commands = self.platform.commands
        self.running.set()

        self.accept_thread.start()
        self.main()

    def main(self):
        while self.running.is_set():
            with self.poll_lock:
                event_list = self.poll.poll(100)
            for event in event_list:
                self.__handle_socket_fd(event)
        self.__cleanup()

    __poll_mask = (select.POLLIN | select.POLLPRI | select.POLLERR |
            select.POLLHUP | select.POLLNVAL)
    def __register_socket(self, socket):
        with self.poll_lock:
            self.poll.register(socket, self.__poll_mask)
            self.socket_list.add(socket)

    def __unregister_socket(self, socket):
        with self.poll_lock:
            self.poll.unregister(socket)
            self.socket_list.discard(socket)

    def __handle_socket_fd(self, event):
        socket_handler, event_mask = event

        if event_mask & (select.POLLPRI | select.POLLIN):
            command = self.__receive_command(socket_handler)
            result = self.__handle_command(command)
            socket_handler.put(result)
        if event_mask & select.POLLOUT:
            message = socket_handler.get()
            socket_handler.send(message)

        if event_mask & select.POLLHUP:
            error = "Unexpected disconnect from client."
        if event_mask & select.POLLERR:
            error = "Unknown error condition."
        if event_mask & select.POLLNVAL:
            error = "Invalid request, descriptor not open."

        if error:
            self.__unregister_socket(socket_handler)
            raise PlatformSocketError(error)

    def __receive_command(self, socket_handler):
        command = socket_handler.recv()
        return command

    def __handle_command(self, command):
        if command == "TERMINATE":
            self.running = False
            return False
        if command == None:
            return False
        logging.debug(command)
        result = ("RESPONSE", self.__run_command(command))
        return result

    def __run_command(self, command):
        return self.commands.run_command(command)

    def __cleanup()
        for socket in self.socket_list:
            self.__unregister_socket(socket)
            socket.close()

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
            handler.fire(event)

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
    def init_server(self, address=None, port=None):

        self.server = PlatformSocketServer(address, port)
        self.serverinfo = (self.server.address, self.server.port)

    def init_platform(self, manifest_file):
        self.platform = Platform(manifest_file, self.server)
        self.server.platform = self.platform
        return

    ## If running locally as a thread or process, start the thread/process and
    #  return to calling context.
    #
    def detach(self):
        pass

    ## Initiate and return connection to a remote PlatformServer.
    #
    def establish_connection(self, serverinfo=None):
        self.connection = PlatformSocketClient(self.serverinfo)
        return self.connection

    ## Launch given UI main() with the given args.
    #
    def launch_ui(self):
        pass

    ## Stop PlatformServer backend.
    #
    def terminate(self):
        pass
