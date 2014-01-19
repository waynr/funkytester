#!/usr/bin/env python

from lib.interface import (
        ADAMInterface,
        )

import lib.module

from adam_module_examples import (
        ADAM_4017P,
        ADAM_4024,
        ADAM_4050,
        ADAM_4051,
        ADAM_4068,
        )

import unittest

class TestADAMModules(unittest.TestCase):
    adam        = ADAMInterface(baud=9600, serial_dev="/dev/ttyS2")
    adam4017p   = ADAM_4017P(adam, "01")
    adam4024    = ADAM_4024(adam, "06")
    adam4050    = ADAM_4050(adam, "04")
    adam4051    = ADAM_4051(adam, "03")
    adam4068    = ADAM_4068(adam, "05")
 
    def tearDown(self,):
        self.adam4050.set_hex("00")
        self.adam4068.set_hex("00")

    def test_4024_digital_in(self,):
        # assumes :
        #  ADAM 4024 VOut1 <-> ADAM 4024 DI 0
        #  ADAM 4024 VOuT2 <-> ADAM 4024 DI 1
        module = self.adam4024

        module.set_analog([2], 5.0)

        module._get_digital()
        inputs  = lib.module.convert_dig2hexstr(
                module.get_digital()["digital_inputs"]
                )

        self.assertEqual(inputs, "02")



    def test_digital_inout(self,):
        dom = self.adam4050
        dim = self.adam4051

        test_values = [
                # test all 1s
                ([0,1,2,3,4,5,6], 1),
                # test all 0s
                ([0,1,2,3,4,5,6], 0),
                # test lsb 1s
                ([0,1,2,3,], 1),
                # reset values
                ([0,1,2,3,4,5,6], 0),
                # test lsb 0, four 1s
                ([4,1,2,3,], 1),
                # reset values
                ([0,1,2,3,4,5,6], 0),
                # test odd alternating 1s
                ([1,3,5,7], 1),
                ([0,1,2,3,4,5,6], 0),
                # test even alternating 1s
                ([0,2,4,6,], 1),
                # set all back to 0
                ([0,1,2,3,4,5,6], 0),
                ]

        for digital, bitvalue in test_values:
            dom.set_digital(digital, bitvalue)
        
            h1      = dom.get_digital()
            h2      = dim.get_digital()

            outputs = lib.module.convert_dig2hexstr(h1["digital_outputs"])
            inputs  = lib.module.convert_dig2hexstr(h2["digital_inputs"][:8])

            self.assertEqual(inputs, outputs)


if __name__ == "__main__":
    unittest.main()
