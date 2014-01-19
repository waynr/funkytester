#!/usr/bin/env python

import sys
sys.path.append("../../")

from interface import get_adam_interface

def cli(adam_interface, debug=True):

    while(True):
        s = raw_input("ADAM> ")
        s = s.lower()

        if s == "help":
            print("(commands: help, query, config)")
            
        elif s == "quit":
            print("Goodbye!")
            break

        elif s == "query":
            delimiter   = raw_input("     delimiter:   ")
            address     = raw_input("     address:     ")
            options     = raw_input("     options:     ")
            result = adam_interface.cmd(
                delimiter   = delimiter,
                address     = address,
                options     = options,
                )
            adam_interface.display_response()

        elif s == "config":
            address     = raw_input("     address:     ")
            #self.config_status(address)
            new         = raw_input("     new address: ")
            type_code   = raw_input("     type code:   ")
            baud_rate   = raw_input("     baud rate:   ")
            extra       = raw_input("     extra:       ")

            result  = adam_interface.cmd(
                delimiter   = "%",
                address     = address,
                options     = type_code + baud_rate + extra,
                )

            adam_interface.display_response()

        else: 
            print("Whoops, invalid command!")

if __name__ == "__main__":
    interface = get_adam_interface("/dev/ttyS3", 9600)
    cli(interface)

