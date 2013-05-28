#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import logging

import fysom

from interfaces import (
        ADAMInterface, 
        ADAM_4068, 
        adam,
        )

## Default action on statechange.
#
def onchangestate(e):
    logging.debug("\'{0}\': \'{1}\' to \'{2}\'.".format( e.event, e.src, 
        e.dst ))

## Abstraction of control over the on/off state of some relay-controlled object.
#
class Relay(fysom.Fysom):

    def __init__(self, relay, pin_list):
        self.relay = relay
        self.pin_list = pin_list
    
        fysom.Fysom.__init__(self, {
            'initial' : 'off',
            'events' : [

                { 'name' : 'disable', 
                    'src' : [ 'on', ],
                    'dst' : 'off' },

                { 'name' : 'enable', 
                    'src' : 'off', 
                    'dst' : 'on' },

                ],
            'callbacks' : {
                'onchangestate' : onchangestate,
                'onenteron' : self.__power_up,
                'onenteroff' : self.__power_down,
                },
            } )

    def __power_up(self, e):
        self.relay.set_digital(self.pin_list, 1)

    def __power_down(self, e):
        self.relay.set_digital(self.pin_list, 0)

class UUTState(fysom.Fysom):

    def __init__(self,):
        fysom.Fysom.__init__(self, {
            'initial' : 'poweroff',
            'events' : [

                { 'name' : 'powerdown', 
                    'src' : [ 'linux', 'uboot', 'null', 'sambam', ],
                    'dst' : 'poweroff' },

                { 'name' : 'pusambam', 
                    'src' : 'poweroff', 
                    'dst' : 'sambam' },

                { 'name' : 'puuboot', 
                    'src' : 'poweroff', 
                    'dst' : 'uboot' },

                { 'name' : 'btlinux', 
                    'src' : 'uboot', 
                    'dst' : 'linux' },

                ],
            'callbacks' : {
                'onchangestate' : onchangestate,
                },
            } )


