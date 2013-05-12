#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

from test.emac_devices import (
        Log,
        BinaryCall,
        )

import unittest
import xmlrpclib

class TestLog(unittest.TestCase):

    def setUp(self,):
        self.log    = Log("output_file.txt")
        s           = xmlrpclib.ServerProxy('http://10.0.2.105:8000')

    def testLog_getmacaddr(self,):
        log = self.log
        testdata = "70:71:bc:87:80:ce" 

        s   = log.get_macaddr(interface_name="eth1")

        self.assertEqual(s, testdata) 

    def testBinaryCall_call(self,):
        testdata    ="""
config
include
lib
Makefile
meta
py.kermit
pylib
py_test
py_test.d
py_test.o
py_test.tar.gz
README
static
templates
whatever
        """

        binary_call = BinaryCall("output_file.txt", binary_full_path=
                "ls")

        output      = binary_call.call(arglist=["../"])
        self.assertEqual('\n' + output[0], testdata)

    

if __name__ == "__main__":
    unittest.main()
