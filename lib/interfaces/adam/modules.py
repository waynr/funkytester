#!/usr/bin/env python

from base import (
        ADAMDigitalInModule,
        ADAMDigitalOutModule,
        ADAMAnalogInModule,
        ADAMAnalogOutModule,
        )

class ADAM_4017P(ADAMAnalogInModule):
    def __init__(self, adam_interface, address="00"):
        ADAMAnalogInModule.__init__(self, adam_interface, address)

class ADAM_4024(ADAMAnalogOutModule, ADAMDigitalInModule):
    def __init__(self, adam_interface, address="00"):
        ADAMAnalogOutModule.__init__(self, adam_interface, address)
        #ADAMDigitalInModule.__init__(self, adam_interface, address,
                #digital_ins=4)

class ADAM_4050(ADAMDigitalOutModule, ADAMDigitalInModule):
    def __init__(self, adam_interface, address="00"):
        ADAMDigitalOutModule.__init__(self, adam_interface, address)
        ADAMDigitalInModule.__init__(self, adam_interface, address,
                digital_ins=7)

class ADAM_4051(ADAMDigitalInModule):
    def __init__(self, adam_interface, address="00"):
        ADAMDigitalInModule.__init__(self, adam_interface, address,
                digital_ins=16)

class ADAM_4068(ADAMDigitalOutModule):
    def __init__(self, adam_interface, address="00"):
        ADAMDigitalOutModule.__init__(self, adam_interface, address)
