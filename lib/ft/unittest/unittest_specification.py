#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import unittest, os, tempfile, shutil, copy

import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

import ft
from ft.device.emac_devices import *

class SpecTest(unittest.TestCase):
    def setUp(self,):
        self.testing_dir = tempfile.mkdtemp()
        self.action_correct = {
                "class": BinaryCall,
                "constructor_args": {},
                "kwargs": {},
                "method_name": "call",
                "name": "Correct Action",
                "remote": False,
                "log_output": False,
                "allow_fail": True,
                }

        self.test_bogus = {
                "wrongo": 5,
                }
        self.test_correct = {
                "actionlist": [
                    self.action_correct,
                    ],
                "name": "Correct Test",
                "refdes": ["REF2"],
                "shortdesc": "This test is correct!",
                "valid": False,
                "type": "expect", 
                }

        self.specification_bogus = {
                "helpp": "hi!",
                "list_dude": [
                    "blah",
                    "9 years to life",
                    ],
                }
        self.specification_correct = {
                "name": "somethingsomething!",
                "shortdesc": "somethingsomething!",
                "instructions": "hi!",
                "testlist": [
                    self.test_correct,
                    self.test_correct,
                    ],
                }
        self.load_classes()

    def load_classes(self):
        from ft.test import Specification
        from ft.test import SpecificationError
        self.SpecificationError = SpecificationError
        self.Specification = Specification

    def produce_yaml_file(self, test_dict, file_name):
        file_name = os.path.join(self.testing_dir, file_name)
        with file(file_name, 'w') as f:
            yaml.dump(test_dict, f, Dumper=Dumper)
        return file_name
        
    def tearDown(self,):
        shutil.rmtree(self.testing_dir)
        
class LoadSpecification(SpecTest):
    # When loading a YAML file, three things must happen:
    #  * The YAML file must be converted into a python data structure
    #  * The resulting data structure must be a valid test specification
    #    dictionary.
    #
    
    def setUp(self,):
        SpecTest.setUp(self)
        
    def tearDown(self,):
        SpecTest.tearDown(self)

    def test_correct(self,):
        # A correct yaml test specification is a dictionary with a "testlist"
        # member which references a list of actionlists.
        correct_yaml_file = self.produce_yaml_file(self.specification_correct,
                "whatever")
        print correct_yaml_file
        spec = self.Specification(correct_yaml_file)
        self.assertEqual(self.specification_correct, spec.test_spec)

    #---------------------------------------------------------------------------
    # The Specification class should raise a custom Exception called
    # "SpecificationError" whenever some attribute is missing from the
    # specification file. The following methods will test various cases of this
    # type of specification file error.
    #
    # The SpecificationError exception class will return a helpful message
    # indicating what the problem is.
    #

    def test_spec_testlist_nonempty(self,):
        # This test prevents the Specification class from erroneously loading a
        # specification dictionary with an empty "testlist" member.
        #
        specification = copy.deepcopy(self.specification_correct)
        specification["testlist"] = []
        incorrect_yaml_file = self.produce_yaml_file(specification, "incorrect")
        self.assertRaisesRegexp(self.SpecificationError, ('missing or invalid'
                'testlist in specification'), self.Specification,
                incorrect_yaml_file)
        
    def test_spec_no_testlist(self,):
        # This test prevents the Specification class from erroneously loading a
        # specification dictionary with a missing "testlist" member.
        #
        specification = copy.deepcopy(self.specification_correct)
        specification.pop("testlist")
        incorrect_yaml_file = self.produce_yaml_file(specification, "incorrect")
        self.assertRaisesRegexp(self.SpecificationError, ('missing or invalid'
                'testlist in specification'), self.Specification,
                incorrect_yaml_file)
        
    def test_spec_has_shortdesc(self,):
        # Checks that the test spec loading process will fail if given a
        # specification file missing a "shortdesc" for the test spec itself.
        #
        specification = copy.deepcopy(self.specification_correct)
        specification.pop("shortdesc")
        incorrect_yaml_file = self.produce_yaml_file(specification, "incorrect")
        self.assertRaisesRegexp(self.SpecificationError, ('missing or invalid'
                'shortdesc in specification'), self.Specification,
                incorrect_yaml_file)

    def test_spec_has_name(self,):
        # This test prevents the Specification class from erroneously loading a
        # specification dictionary with no "name" member.
        #
        specification = copy.deepcopy(self.specification_correct)
        specification.pop("name")
        incorrect_yaml_file = self.produce_yaml_file(specification, "incorrect")
        self.assertRaisesRegexp(self.SpecificationError, ('missing or invalid'
                'name in specification'), self.Specification,
                incorrect_yaml_file)

    def test_spec_testlist_has_name(self,):
        # This test prevents the Specification class from erroneously loading a
        # specification dictionary with a testlist that has no "actionlist"
        # member.
        #
        specification = copy.deepcopy(self.specification_correct)
        specification["testlist"][0]["actionlist"] = []
        incorrect_yaml_file = self.produce_yaml_file(specification, "incorrect")
        self.assertRaisesRegexp(self.SpecificationError, ('missing or invalid'
                'actionlist in specification'), self.Specification,
                incorrect_yaml_file)
        
        
