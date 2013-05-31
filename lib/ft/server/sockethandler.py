#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#

import logging, threading

try:
    import cPickle as pickle
except ImportError:
    import pickle

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
    __HEADER_SIZE += field[1] 
__HEADER_SIZE += len(__HEADER_FORMAT_LIST) - 1

class PlatformSocketError(Exception)

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)

## Implement static length header to provide actual message size to receiver.
#
class SocketDataHandler(object):
    
    def __init__(self, socket, address=None):
        self.__socket = socket
        self.address = address

    def fileno(self):
        return self.__socket.fileno()

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
        if not isinstance(self.__socket, socket.Socket):
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
            tmp = self.__socket.send(message[sent_bytes:])
            if tmp == 0:
                raise RuntimeError("Socket connection lost!")
            sent_bytes += tmp

    def __receive_message(self, size):
        msg = ''
        msglen = len(msg)
        while msglen < size:
            chunk = self.__socket.recv(size - msglen)
            if chunk == '':
                raise RuntimeError("Socket connection lost!")
            msg += chunk
            msglen = len(msg)
        return msg

## Pickles object before using SocketDataHandler send/recv
#
class SocketObjectHandler(SocketDataHandler):

    def __init__(self, *args, **kwargs):
        super(SocketObjectHandler, self).__init__(*args, **kwargs)

    def send(self, obj):
        message = pickle.dumps(obj, pickle.HIGHEST_PROTOCOL)
        SocketDataHandler.send(self, message)

    def recv(self, obj):
        message = SocketDataHandler.recv(self, message)
        return pickle.loads(message)
