#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

from os import path, walk
import sys, logging

import yaml
try:
        from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
        from yaml import Loader, Dumper

## Loads a yaml file as a Python dictionary
#
# Also checks that the resulting dictionary has the appropriate 
# format (ie: includes the necessary members: testlist, name, a 
# short description, and action list)
#
class Specification(object,):

    ## The constructor
    #
    # Checks that the loaded file is of the correct format
    #
    # @param self The object pointer
    # @param specification_file_name Pointer to the file to be loaded
    #
    def __init__(self, specification_file_name ):
        self.test_spec = self.load(specification_file_name)
        Specification.check(self)

    ## Tests the loaded dictionary test_spec for correct format
    #
    # @param self The object pointer
    #
    def check(self):

        ## A list of required members in a specification dictionary
        #
        required = ['testlist', 'shortdesc', 'name']

        for member in required:
            self.check_for_member(self.test_spec, member)
            self.check_member_nonempty(self.test_spec, member)

        # This may become deprecated, dependent on the checks in action.py
        # For now, it does what we need it to do.
        self.check_for_member(self.test_spec["testlist"][0], "actionlist")
        self.check_member_nonempty(self.test_spec["testlist"][0], "actionlist")

    ## Loads a file as a Python dictionary
    # 
    # Checks that the input file is a yaml file by catching any yaml exceptions
    #
    # @param self The object pointer
    # @param file_name Pointer to the file to be loaded
    #
    def load(self, file_name="default_test"): 
        try:
            with file(file_name, 'r+') as f:
                tmp = yaml.load(f, Loader=Loader)
            return tmp
        except yaml.YAMLError as exc:
            # This file is not a yaml file, move on to the next file
            if hasattr(exc, "problem_mark"):
                mark    = exc.problem_mark
                loc     = " ({0}, {0})".format(mark.line+1, mark.column+1)
            else:
                loc     = ""
            logging.warn("Error in configuration file, {0}.{1}".format(
                file_name, loc))
        except:
            raise

    ## Checks that the given member exists in the dictionary
    #
    # Raises a SpecificationError if the member does not exist
    #
    # @param self The object pointer
    # @param dictionary The dictionary to check
    # @param member The member we seek
    #
    def check_for_member(self, dictionary, member):
        if dictionary.has_key(member):
            pass
        else:
            raise SpecificationError(member)

    ## Checks that a given member in the dictionary is not empty
    #
    # Raises a SpecificationError if the member is empty
    #
    # @param self The object pointer
    # @param dictionary The dictionary to check
    # @param member The member we are checking
    #
    def check_member_nonempty(self, dictionary, member):
        if dictionary[member] == []:
            raise SpecificationError(member)

## An Exception class that handles Specification-specific errors
#
# Formats the error's message
#
class SpecificationError(Exception):

    ## The constructor
    #
    # @param self The object pointer
    # @param member The member of the Specification that established the error
    #
    def __init__(self, member):
        self.message = ("missing or invalid%s in specification") % member

    ## Gives a string representation of the exception
    #
    # @self The object pointer
    #
    def __str__(self):
        return repr(self.message)
