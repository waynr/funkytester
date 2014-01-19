#!/usr/bin/env python

import sys
import re

def isDelimiter(delimiter):
    if not delimiter in '$#%@':
        return False

    if len(delimiter) > 1:
        return False 

    return True

def isAddress(address):
    return re.match("[0-9a-fA-F]{2}", address)
