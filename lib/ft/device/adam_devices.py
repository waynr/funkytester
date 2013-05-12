#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import sys
import logging

from interfaces.adam import (
        adam_interface,
        ADAM_4017P,
        ADAM_4024,
        ADAM_4050,
        ADAM_4051,
        ADAM_4068,
        )

class ADAM_4024_action(ADAM_4024):
    def __init__(self, kwargs):
        address = kwargs["address"]
        adam_interface = adam_interface()
        ADAM_4024.__init__(self, adam_interface, address)

    def set_analog(self, kwargs):
        channel_list    = kwargs["channel_list"]
        value           = kwargs["value"]

        result  = ADAM_4024.set_analog(self, channel_list=channel_list, 
                float_value=value)

        return result, " "

class ADAM_4050_action(ADAM_4050):
    def __init__(self, kwargs):
        address = kwargs["address"]
        adam_interface = adam_interface()
        ADAM_4050.__init__(self, adam_interface, address)

    def get_hexval(self, kwargs):
        if kwargs.has_key("t"):
            t   = kwargs["t"]
            if t == "inputs" or t == "outputs":
                return self.hexvals[t]

        return self.hexvals
        
    def get_hex(self, kwargs):
        output_type     = kwargs["t"]
        if kwargs.has_key("invert_input"):
            invert_input    = kwargs["invert_input"]
        else:
            invert_input    = False

        result  = ADAM_4050.get_hex(self, t=output_type, invert_input=invert_input)

        return result, " "

    def set_hex(self, kwargs):
        value   = kwargs["value"]

        if kwargs.has_key("invert_output"):
            invert_output   = kwargs["invert_output"]
        else:
            invert_output   = False

        result  = ADAM_4050.set_hex(self, hexstr=value, invert_output=invert_output)

        return result, " "

class ADAM_4051_action(ADAM_4051):
    def __init__(self, kwargs):
        address = kwargs["address"]
        adam_interface = adam_interface()
        ADAM_4051.__init__(self, adam_interface, address)
        
    def get_digital(self, kwargs):
        output_type         = kwargs["t"]

        if kwargs.has_key("selection"):
            selection   = kwargs["selection"]
        else:
            selection   = None

        if kwargs.has_key("invert_input"):
            invert_input    = kwargs["invert_input"]
        else:
            invert_input    = False

        result  = ADAM_4051.get_digital(self, t=output_type, selection=selection) 

        return result, " "

    def get_hex(self, kwargs):
        output_type     = kwargs["t"]
        if kwargs.has_key("invert_input"):
            invert_input    = kwargs["invert_input"]
        else:
            invert_input    = False

        result  = ADAM_4051.get_hex(self, t=output_type, invert_input=invert_input)

        return result, " "

class ADAM_4068_action(ADAM_4068):
    def __init__(self, kwargs):
        address = kwargs["address"]
        adam_interface = adam_interface()
        ADAM_4068.__init__(self, adam_interface, address)

    def set_digital(self, kwargs):
        value       = kwargs["value"]
        channels    = kwargs["channels"]

        if kwargs.has_key("invert_output"):
            invert_output   = kwargs["invert_output"]
        else:
            invert_output   = False

        result  = ADAM_4068.set_digital(self, channels, value)

        return result, " "

