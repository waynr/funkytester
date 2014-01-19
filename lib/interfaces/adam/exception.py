#!/usr/bin/env python

class ADAMError(Exception):

    def __init__(self):
        self.message = "No ADAMInterface found!"

    def __str__(self):
        return repr(self.message)
