#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import os, os.path as path
import unittest, sys, optparse, re

req_version = (2, 7)
cur_version = sys.version_info

if cur_version < req_version:
    print("Need python version > 2.7.X")
    sys.exit(-1)

bindir = path.dirname(__file__)
topdir = path.dirname(bindir)
libdir = path.join(topdir, "lib")
extdir = path.join(topdir, "ext")

sys.path.insert(0, libdir)
sys.path.insert(0, extdir)
sys.path.insert(0, topdir)
import pytest

def parse_options():
    option_parser = optparse.OptionParser(
            version = "EMAC Functional Test, verison {0}".format(
                pytest.__version__),
            usage = """%prog [options] <TEST_DIR>""",
            )
    option_parser.add_option("-q", "--quiet", 
            help="Turn off non-UI test output.",
            action="store_false", 
            dest="verbose",
            )
    option_parser.set_defaults(
            verbose         = False,
            )
    option_parser.add_option("-d", "--start-dir", 
            help="Set the start directory to begin looking for unittests.",
            action="store", 
            type="string",
            dest="start_dir",
        )
    option_parser.set_defaults(
            verbose = False,
            start_dir = "./lib/ft/unittest",
            )
    
    return option_parser

def main():
    option_parser = parse_options()
    (options, args) = option_parser.parse_args()

    testloader = unittest.TestLoader()

    achievo_tests = testloader.discover("achievo/unittest", 'unittest.*py',
            'ext')
    ft_tests = testloader.discover("ft/unittest", 'unittest.*py',
            'lib')

    testrunner = unittest.runner.TextTestRunner()
    for tests in [ achievo_tests, ft_tests]:
        testrunner.run(tests)

if __name__ == "__main__":
    try:
        ret = main()
    except Exception:
        ret = 1
        import traceback
        traceback.print_exc(5)
    sys.exit(ret)
