#!/usr/bin/env python

## @package eserial
#  Create enhanced serial port capability using a thread to facilitate
#  asynchronous operations on input buffers such as "read_until".
#
#  Copyright Wayne Warren, 2013 waynr@sdf.org
#  GPLv2
#

import pprint, threading, re, traceback, logging, os, termios

import serial, fdpexpect

## Use regex to determine whether or a match exists in the given string list. 
#
def check_string_list(regex, string_list):
    for s in string_list:
        match   = re.match(regex, s) 
        if not match == None:
            return True
    return False

## Augment basic serial.Serial class.
#
class EnhancedSerial():
    def __init__(self, serial_port, baud_rate, *args, **kwargs):
        self.serial_port = serial_port
        self.baud_rate = baud_rate

    class fdpexpect:
        lock = threading.Lock()

        def __init__(self, serial_port, baud_rate):
            self.serial_port = serial_port
            
            baud_rate = "B" + str(baud_rate)
            if hasattr(termios, baud_rate):
                self.baud_rate = getattr(termios, baud_rate)
            else:
                raise ValueError("Invalid baud_rate: " + baud_rate)

        def __enter__(self):
            self.lock.acquire()
            self.fd = os.open(self.serial_port, os.O_RDWR|os.O_NONBLOCK|os.O_NOCTTY)
            attr_list = termios.tcgetattr(self.fd)
            attr_list[1] &= ~termios.ONLCR
            attr_list[3] &= ~termios.ECHO
            attr_list[3] &= ~termios.ICANON
            attr_list[4] = self.baud_rate
            attr_list[5] = self.baud_rate
            attr_list[6][termios.VTIME] = 5
            termios.tcsetattr(self.fd, termios.TCSAFLUSH, attr_list)
            
            return fdpexpect.fdspawn(self.fd)

        def __exit__(self, type, value, traceback):
            os.close(self.fd)
            self.lock.release()
            return True

    def setup(self):
        self.fd = os.open(self.serial_port, os.O_RDWR|os.O_NONBLOCK|os.O_NOCTTY)

    def release(self):
        self.fd = None

    # dummy function
    def start(self):
        pass

    ## Prepare to begin searching all unread input for some given regex.
    #
    #  @param regex The regular expression used to match against the lines in
    #   the "unread" buffer. Typically a prompt used to determine that the given
    #   command was successful.
    #  @param command Optional; A command to be run after flushing the "unread"
    #   and the "read" buffers into the EnhancedSerial history buffer. This
    #   command is run after flushing to avoid missing any of the command's
    #   output that might end up in the history buffer.
    #  @param timeout The amount of time to wait for the regex to match against
    #   a line in the unread buffer.
    #  @param debug Currently unused. Kept for backwards compatibility with old
    #   EnhancedSerial class.
    #
    def read_until(self, regex, command=None, timeout=10, debug=False):
        with self.fdpexpect(self.serial_port, self.baud_rate) as m:
            if not command:
                result = m.expect(regex, timeout)
                return result
    
            try:
                if debug:
                    print("regex: " + str(regex))
                m.send(command)
                result = m.expect(regex, timeout)
                if debug:
                    print("result: " + str(result))
                    print("-c-")
                    print(command)
                    print("-b-")
                    print(m.before)
                    print("-a-")
                    print(m.after)
            except fdpexpect.TIMEOUT:
                if debug:
                    print("-c-")
                    print(command)
                    print("-b-")
                    print(m.before)
                    print("-a-")
                    print(m.after)
                return False, m.before
            except fdpexpect.EOF:
                return False, m.before
            
            if result == 0:
                return True, m.before

class OldEnhancedSerial(serial.Serial,):
    def __init__(self, *args, **kwargs):
        #ensure that a reasonable timeout is set
        timeout = kwargs.get('timeout',0.1)
        if timeout < 0.01: timeout = 0.1
        kwargs['timeout'] = timeout
        super(OldEnhancedSerial, self).__init__(*args, **kwargs)
        self.buf = ''
        self.dbg = 1

    def read_until(self, match, timeout=1, debug=1):
        tries = 0
        buf = ""

        self.dbg = debug

        while True:
            tmp = self.read(4096)

            if tmp:
                buf += tmp
            if match in tmp:
                return True, buf

            tries += 1
            if tries * self.timeout > timeout:
                break

        return False, buf


    def readline(self, maxsize=None, timeout=1):
        """maxsize is ignored, timeout in seconds is the max time that is way for a complete line"""
        tries = 0
        while 1:
            self.buf += self.read(512)
            pos = self.buf.find('\n')
            if pos >= 0:
                line, self.buf = self.buf[:pos+1], self.buf[pos+1:]
                return line
            tries += 1
            if tries * self.timeout > timeout:
                break
        line, self.buf = self.buf, ''
        return line

    def readlines(self, sizehint=None, timeout=1):
        """read all lines that are available. abort after timout
        when no more data arrives."""
        lines = []
        while 1:
            line = self.readline(timeout=timeout)
            if line:
                lines.append(line)
            if not line or line[-1:] != '\n':
                break
        return lines

if __name__ == "__main__":
    ser   = EnhancedSerial(port="/dev/ttyUSB0", baudrate=115200)
    ser.start()
    #status, s   = ser.read_until('macb0', timeout=100)
    status, s   = ser.read_until('DaVinci EMAC', timeout=100)
    print(s)
    status, s   = ser.read_until('U-Boot>', command='\n', timeout=100)
    print(s)
    status, s   = ser.read_until('U-Boot>', command='printenv\n', timeout=100)
    print(s)
    status, s   = ser.read_until('U-Boot>', timeout=100)
    print(s)

