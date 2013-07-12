#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import Queue as StdLibQueue, threading, logging, os, socket, select
from multiprocessing import Queue

import ft.event
from ft.platform import Platform

from ft.server.sockethandler import QueuedSocketHandler, SocketObjectHandler
from ft.server.common import PlatformClient, EventHandlerRegistry

class PlatformSocketClient(PlatformClient):

    def __init__(self, server_info, *args, **kwargs):
        super(PlatformSocketClient, self).__init__(*args, **kwargs)

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.connect(server_info)

        self.socket_handler = SocketObjectHandler(self.server)

    def _receive_message(self):
        readable, writable, exceptional = select.select(
            [self.socket_handler], [] , [], 0)
        if not len(readable) == 0:
            message = self.socket_handler.recv()
            return message
        return None

    def _handle_message(self, message):
        if isinstance(message, ft.event.Event):
            logging.debug(message)
            self.handler_registry.fire(message)
        elif message[0] == "RESPONSE":
            self.incoming_queue.put(message[1])
        else:
            logging.error("Unhandled PlatformServer message: "
                          "{0}".format(message))

    def _get_outgoing_item(self):
        try:
            return self.outgoing_queue.get(False)
        except StdLibQueue.Empty:
            return None

    def _handle_outgoing_queue(self):
        command = self._get_outgoing_item()
        if command:
            readable, writable, exceptional = select.select(
                [], [self.socket_handler], [], 0)
            if len(writable) > 0:
                self.socket_handler.send(command)

class PlatformSocketServer(threading.Thread):

    def __init__(self, address, port):
        super(PlatformSocketServer, self).__init__(
            name="PlatformSocketServerMain")
        self.address = address
        self.port = port

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((address, port))
        self.socket.listen(3)
        self.socket_dict = {}

        self.poll_lock = threading.RLock()
        self.poll = select.poll()

        self.accept_thread = threading.Thread(target=self.__acceptor,
            name="PlatformSocketServerAcceptor")
        self.accept_thread.daemon = True

        self.running = threading.Event()

        self.commands = None
        self.platform = None # is set externally
        self.event_registry = EventHandlerRegistry()

    def fire(self, event, **kwargs):
        e = event(**kwargs)
        for socket_fd, socket_handler in self.socket_dict.items():
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
            self.socket_dict[socket.fileno()] = socket

    def __unregister_socket(self, socket):
        with self.poll_lock:
            self.poll.unregister(socket)
            self.socket_dict.pop(socket.fileno)

    def __handle_socket_fd(self, event):
        socket_fd, event_mask = event
        socket_handler = self.socket_dict[socket_fd]

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
            self.running.clear()
            return False
        if command == None:
            return False
        logging.debug(command)
        result = ("RESPONSE", self.__run_command(command))
        return result

    def __run_command(self, command):
        return self.commands.run_command(command)

    def __cleanup():
        for socket_fd, socket_handler in self.socket_dict.items():
            self.__unregister_socket(socket_handler)
            socket.close()

## PlatformServer is an interface wraps some type of server to provide a
#  consistent API during program startup so that different server
#  implementations can be used with relatively little difficulty using the same
#  code.
#
class PlatformServer(object):

    ## Initialize the daemon which will control the platform during testing, and
    #  if applicable to server type set "serverinfo" tuple.
    #
    def init_server(self, options):

        address = options.platform_server_host
        port = options.platform_server_port

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
        self.server.start()
        return

    ## Initiate and return connection to a remote PlatformServer.
    #
    def establish_connection(self, serverinfo=None):
        self.connection = PlatformSocketClient(self.serverinfo)
        return self.connection

    ## Launch given UI main() with the given args.
    #
    def launch_ui(self, uifunc, *args):
        return  uifunc(*args)

    ## Stop PlatformServer backend.
    #
    def terminate(self):
        pass
