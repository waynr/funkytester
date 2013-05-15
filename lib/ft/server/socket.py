#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import Queue as StdLibQueue, threading, logging, os, socket, hashlib
from multiprocessing import Queue

import ft.event
from ft.platform import Platform

__MAX_CLIENTS = 1

__HASH_FUNCTION = hashlib.md5

def __get_len(message):
    return len(message)

def __get_hexdigest(message):
    m = __HASH_FUNCTION()
    m.update(message)
    return m.hexdigest()

m = __HASH_FUNCTION()
m.update(" ")
__HASH_DIGESTLEN = len(m.hexdigest())

__HEADER_FIELD_DELIMITER = ','
__HEADER_FORMAT_LIST = [
        ("0:0>{width}d", 16, __get_len),
        ("0:0>{width}s", __HASH_DIGESTLEN, __get_hexdigest),
        ]

( __HFIELD_SIZE, 
        __HFIELD_DIGEST,
        ) = range(2)

def __get_header(message):
    header = ""
    for field in __HEADER_FORMAT_LIST:
        field = field[0].format(field[2](message), width=field[1])
        header += field + __HEADER_FIELD_DELIMITER
    return header[:1]

def __parse_header(header):
    return header.split(__HEADER_FIELD_DELIMITER)

__HEADER_SIZE = 0
for field in __HEADER_FORMAT_LIST:
    __HEADER_SIZE += field[1] + len(__HEADER_FIELD_DELIMITER)

class SocketDataHandler(object):

    def send(self, message):
        self.__check_socket()
        self.__send_header(message)
        self.__send_message(message)

    def recv(self):
        self.__check_socket()

        header = self.__receive_header()
        message = self.__receive_message(header[__HFIELD_SIZE])
        check = __parse_header(__get_header(message))

        assert header == check

        return message

    def __check_socket(self):
        if not isinstance(self.socket, socket.Socket):
            raise AttributeError("Socket object not available.")

    def __send_header(self, message):
        header = __get_header(message)
        self.__send_message(header)

    def __receive_header(self):
        header = self.__receive_message(__HEADER_SIZE)
        return __parse_header(header)

    def __send_message(self, message):
        message_size = len(message)
        sent_bytes = 0
        while sent_bytes < message_size:
            tmp = self.socket.send(message[sent_bytes:])
            if tmp == 0:
                raise RuntimeError("Socket connection lost!")
            sent_bytes += tmp

    def __receive_message(self, size):
        msg = ''
        msglen = len(msg)
        while msglen < size:
            chunk = self.socket.recv(size - msglen)
            if chunk == '':
                raise RuntimeError("Socket connection lost!")
            msg += chunk
            msglen = len(msg)
        return msg

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
