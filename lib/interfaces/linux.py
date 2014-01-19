#!/usr/bin/env python

import logging

from serial import SerialInterface

class LinuxTerminalInterface(SerialInterface):

    __prompt = { 
            "username" : "^.*login:",
            "password" : "Password:"
            }

    def __init__(self, prompt, *args, **kwargs):
        SerialInterface.__init__(self, *args, **kwargs)
        self.prompt = prompt

    def login(self, user = "root", password = "emac_inc"):
        serial  = self.serial

        # make sure we have the "login" prompt

        prompt  = self.__prompt["username"]
        test, tmp = serial.read_until(prompt, timeout = 120)

        if test:
            serial.write(user)
            serial.write("\n")

        prompt  = self.__prompt["password"]
        test, tmp = serial.read_until(prompt, timeout = 2)

        if test:
            serial.write(password)
            serial.write("\n")

        prompt  = self.prompt
        test, tmp = serial.read_until(prompt, timeout = 20)

        if test:
            return True

        return False

