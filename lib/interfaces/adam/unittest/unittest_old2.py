#!/usr/bin/env python

from interface import (
        ADAMInterface,
        )

from module import (
        ADAMModule,
        ADAMAnalogModule,
        ADAMAnalogInModule,
        ADAMAnalogOutModule,
        ADAMDigitalModule,
        ADAMDigitalOutModule,
        ADAMDigitalInModule,
        convert_dig2int,
        convert_dig2hexstr,
        convert_int2hexstr,
        convert_float2data,
        )

import unittest
import time

class TestADAMAnalogModule(unittest.TestCase):
    adam    = ADAMInterface(baud=9600, serial_dev="/dev/ttyS2")

    def setUp(self,):
        self.dm = ADAMAnalogModule(self.adam, "06")

    def test_convert_float2data_badvalue(self,):
        test_values = [
                200,
                100,
                -100,
                -200,
                ]
        for value in test_values:
            self.assertRaises(ValueError, convert_float2data, value)

    def test_convert_float2data_badtype(self,):
        test_values = [
                3j,
                "blah",
                [1,2],
                {"hello":0},
                ]
        for value in test_values:
            self.assertRaises(TypeError, convert_float2data, value)

    def test_convert_float2data_good(self,):

        test_values = [
                (0, "+00.000"),
                (0.0, "+00.000"),
                (0.0002, "+00.000"),
                (3, "+03.000"),
                (3.4200234, "+03.420"),
                (13, "+13.000"),
                (-0.0, "-00.000"),
                (-3.4, "-03.400"),
                (-3.4000234, "-03.400"),
                (-8.493, "-08.493"),
                ]

        for f, expected_result in test_values:
            data    = convert_float2data(f)
            self.assertEqual(expected_result, data)

class TestADAMAnalogInOutModule(unittest.TestCase):

    adam    = ADAMInterface(baud=9600, serial_dev="/dev/ttyS2")

    def setUp(self,):
        # this test assumes that ADAM 4024 Channel 0 is connected to ADAM 4017P
        # Channel 5
        self.ao = ADAMAnalogOutModule(self.adam, "06")
        self.ai = ADAMAnalogInModule(self.adam, "01")
        self.ao._set_analog(0, 0.0)
        time.sleep(1)

    def test_inout(self,):
        ao  = self.ao
        ai  = self.ai

        test_values  = [
                -2.56,
                0.0,
                1.999,
                1.001,
                2.30,
                8.9,
                9.9,
                ]

        for test_value in test_values:
            ao._set_analog(0, test_value)
            time.sleep(.5)

            outs    = ao.get_analog()["analog_outputs"]
            ins     = ai.get_analog()["analog_inputs"]

            #print(outs, ins)

            self.assertAlmostEqual(outs[0], ins[5], 2)
            self.assertAlmostEqual(outs[0], test_value, 2)

class TestADAMDigitalModule(unittest.TestCase):

    adam    = ADAMInterface(baud=9600, serial_dev="/dev/ttyS2")

    def setUp(self,):
        self.dm = ADAMDigitalOutModule(self.adam, "02")
        self.initial    = "AA"
        self.dm.set_hex(self.initial)

    def test_read(self):
        dm      = self.dm

        current = dm.get_digital()["digial_outputs"]
        hstr    = convert_dig2hexstr(current)

        self.assertEqual(self.initial, hstr, 
                "Test data ({0}) does not match current value ({1})" 
                .format(self.initial, hstr))
        
class TestADAMDigitalInModule(unittest.TestCase):

    adam    = ADAMInterface(baud=9600, serial_dev="/dev/ttyS2")

    def setUp(self,):
        # ADAM 4050
        self.dom = ADAMDigitalOutModule(self.adam, "04", 8)
        # ADAM 4051
        self.dim = ADAMDigitalInModule(self.adam, "03", 16)

        # WARNING: This testsuite requires that outputs 0-7 on the ADAM-4050 be
        # connected to inputs 0-7 on the ADAM-4051.

    def test_read_1(self):
        dom = self.dom
        dim = self.dim

        test_values = [
                # test all 1s
                ([0,1,2,3,4,5,6,7], 1),
                # test all 0s
                ([0,1,2,3,4,5,6,7], 0),
                # test lsb 1s
                ([0,1,2,3,], 1),
                # reset values
                ([0,1,2,3,4,5,6,7], 0),
                # test lsb 0, four 1s
                ([4,1,2,3,], 1),
                # reset values
                ([0,1,2,3,4,5,6,7], 0),
                # test odd alternating 1s
                ([1,3,5,7], 1),
                ([0,1,2,3,4,5,6,7], 0),
                # test even alternating 1s
                ([0,2,4,6,], 1),
                # set all back to 0
                ([0,1,2,3,4,5,6,7], 0),
                ]

        for digital, bitvalue in test_values:
            dom.set_digital(digital, bitvalue)
        
            h1      = dom.get_digital()
            h2      = dim.get_digital()

            outputs = convert_dig2hexstr(h1["digial_outputs"])
            inputs  = convert_dig2hexstr(h2["digial_inputs"][:8])

            self.assertEqual(inputs, outputs)


class TestADAMDigitalOutModule(unittest.TestCase):

    adam    = ADAMInterface(baud=9600, serial_dev="/dev/ttyS2")

    def setUp(self,):
        self.dm = ADAMDigitalOutModule(self.adam, "02")
        self.initial    = "AA"
        self.dm.set_hex(self.initial)

    def tearDown(self,):
        self.dm.set_hex("00")

    def test_set_digital_0(self):
        dm  = self.dm

        lst     = [0,1,4,5]

        dm.set_digital(lst, 0)

        h1  = "88"

        h2  = convert_dig2hexstr(dm.get_digital()["digial_outputs"])
        self.compare_registers(h1, h2,)

    def test_set_digital_1(self):
        dm  = self.dm
        h1  = convert_dig2int(dm.get_digital()["digial_outputs"])

        lst     = [0,1,4,5]
        dm.set_digital(lst, 1)

        h1  = "BB"

        h2  = convert_dig2hexstr(dm.get_digital()["digial_outputs"])
        self.compare_registers(h1, h2,)

    def test_set_hex(self):
        dm  = self.dm

        hexstr      = "08"
        dm.set_hex(hexstr)

        h1  = dm.get_digital()["digial_outputs"]
        cur_hex     = convert_dig2hexstr(h1)

        self.assertEqual(hexstr, cur_hex, "Test data ({0}) does not match \
current value ({1})".format(hexstr, cur_hex))


    def test_set_mask_1(self):
        dm  = self.dm

        dm.set_mask("F4", 1)

        h1  = "FE"

        h2  = convert_dig2hexstr(dm.get_digital()["digial_outputs"])
        self.compare_registers(h1, h2,)

    def test_set_mask_0(self):
        dm  = self.dm

        test_values = [
                ("00", "AA",),
                ("30", "8A",),
                ("34", "8A",),
                ("32", "88",),
                ("FF", "00",),
                ]

        for mask, result in test_values:
            dm.set_mask(mask, 0)
    
            h2  = convert_dig2hexstr(dm.get_digital()["digial_outputs"])
            self.compare_registers(result, h2,)

    def test_convert_dig2int_0(self,):
        digital = [0,0,0,0,0,0,0,0,]
        mask    = int("00", 16)

        test    = convert_dig2int(digital)
        self.assertEqual(test, mask, "{0} and {1} are not equal!"
                .format(test, mask, mask))

    def test_convert_dig2int_1(self,):
        digital = [1,1,1,1,1,1,1,1,]
        mask    = int("FF", 16)

        test    = convert_dig2int(digital)
        self.assertEqual(test, mask, "{0} and {1} are not equal!"
                .format(test, mask,))

    def test_convert_dig2int_m1(self,):
        digital = [1,0,1,0,1,0,1,0,]
        mask    = int("AA", 16)

        test    = convert_dig2int(digital)
        self.assertEqual(test, mask, "{0} and {1} are not equal!"
                .format(test, mask,))

    def test_convert_dig2int_m2(self,):
        digital = [0,1,0,1,0,1,0,1,]
        mask    = int("55", 16)

        test    = convert_dig2int(digital)
        self.assertEqual(test, mask, "{0} and {1} are not equal!"
                .format(test, mask,))

    def compare_registers(self, hexstr1, hexstr2):
        # r1 and r2 should be lists of integers representing the values of the
        # digital interface being compared; they are expected to be the same
        # value

        self.assertEqual(hexstr1, hexstr2, 
                "Expected ({0}) does not match current value ({1})" 
                .format(hexstr1, hexstr2))

if __name__ == "__main__":
    unittest.main()
