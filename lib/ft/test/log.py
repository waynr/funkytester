#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
## @package log
#  The purpose of this module is to provide log-to-file capability for
#  individual tests, test groups, and batches of tests/groups.
#  

import csv
from os import path
import datetime
import logging
import pprint

from ft.test.results import (
        TestResult,
        GroupResult,
        STATUS_INIT,
        STATUS_SUCCESS,
        STATUS_SUCCESS_INVALID_INTERFACE,
        STATUS_FAIL,
        STATUS_BROKEN_TEST,
        STATUS_UNKNOWN,
        )

CSV_TEST = [
        "row_type",
        "name",
        "status",
        "refdes",
        ]

CSV_SINGLE_ACTION = [
        "row_type",
        "name",
        "status",
        "output",
        ]

CSV_EXPECT_ACTION = [
        "row_type",
        "name",
        "status",
        "expected_val",
        "actual_val",
        "tolerance",
        ]

def write_csv(f, row_type, row_dict):
    writer  = csv.DictWriter( 
            f,
            row_type,
            dialect = 'excel-tab',
            )
    writer.writerow(row_dict)

def count_fails(group_result):
    count = 0
    for result in group_result.results_list:
        if result.status == STATUS_FAIL:
            count += 1
    return count

class CSVLog(object,):
    def __init__(self, log_dir, serial_number, tester="EMAC Tester", 
            test_facility="EMAC", test_assembly="EMAC Functional Tester"):
        if not path.isdir(log_dir):
            raise OSError("Directory not found: {0}".format(log_dir))
        self.log_dir    = log_dir
        self.serial_number    = serial_number
        self.tester    = tester
        self.test_facility    = test_facility
        self.test_assembly    = test_assembly
        self._set_log_file(log_dir, serial_number)

    def _write_action_expect(self, action_dict):
        row_dict = {
                "row_type"  : "EA",
                "name"   : action_dict["name"],
                "status"    : action_dict["status"],
                "tolerance" : action_dict["tolerance"],
                "expected_val" : action_dict["expected_value"],
                "actual_val" : action_dict["test_value"],
                }
        with open(self.log_file, 'a+') as f:
            write_csv(f, CSV_EXPECT_ACTION, row_dict)

    def _write_action_single(self, action_dict):
        row_dict = {
                "row_type"  : "SA",
                "name"   : action_dict["name"],
                "status"    : action_dict["status"],
                "output" : action_dict["output"],
                }
        with open(self.log_file, 'a+') as f:
            write_csv(f, CSV_SINGLE_ACTION, row_dict)

    def _write_test(self, result):
        test_dict   = result.test_dict
        row_dict   = {
                "row_type" : "T",
                "name" : result.test_name,
                "status" : result.status,
                "refdes" : test_dict["refdes"],
                }
        with open(self.log_file, 'a+') as f:
            write_csv(f, CSV_TEST, row_dict)
            s = "\"{0:-^79}\"\n\n".format('')

    def write_results(self, result):
        self._write_test(result)
        if not result.status == STATUS_SUCCESS:
            method  = getattr(self, "_write_action_" + 
                    result.test_dict["type"])
            for action_result in result.current["results"]:
                method(action_result)

    ## Commit the results of the tests in the current serial's list of tests.
    #
    #  Currently, these are stored in a class attribute of TestResults. This
    #  really needs to be fixed with the introduction of a "Batch" class that
    #  encapsulates all of the tests associated with a given serial number.
    #
    def commit(self, result ):
        test_dict   = result.test_dict
        test_type   = test_dict["type"]

        number_failures = 0

        if test_type == "group":
            number_failures = count_fails(result)
            self.insert_header(number_failures)
            for result in result.results_list:
                self.write_results(result)
        else:
            if result.status == STATUS_FAIL:
                number_failures += 1
            self.insert_header(number_failures)
            self.write_results(result)

    def insert_header(self, number_failures=0):
        with open(self.log_file, 'a+') as f:
            d   = datetime.datetime.now()
            report_date   = d.strftime("%b %d, %Y")
            report_time   = d.strftime("%H:%M")
            serial_number   = self.serial_number

            single_action_format   = "'SA'  " + "  ".join(
                    CSV_SINGLE_ACTION[1:])
            expect_action_format   = "'EA'  " + "  ".join(
                    CSV_EXPECT_ACTION[1:])
            test_format   = "'T'  " + "  ".join(CSV_TEST[1:])

            def fmt_elmnt(element_name, element_value):
                return "    {0:>20}:  {1}\r\n".format(element_name,
                        element_value)
            s = "\t \t \t"
            s = s + "\"{0:-^79}\r\n".format('')
            s = s + "{0:^80}\r\n".format('Functional Test Results Report')
            s = s + fmt_elmnt( 'Test Facility', self.test_facility )
            s = s + fmt_elmnt( 'Test Technician', self.tester )
            s = s + fmt_elmnt( 'Assembly Name', self.test_assembly )
            s = s + fmt_elmnt( 'UUT Serial Number', 
                    self.serial_number.upper() )
            s = s + fmt_elmnt( 'Failures', number_failures )
            s = s + fmt_elmnt( 'Report Date', report_date )
            s = s + fmt_elmnt( '       Time', report_time )
            s = s + fmt_elmnt( 'Test Format', test_format )
            s = s + fmt_elmnt( 'Single Action Format', 
                    single_action_format )
            s = s + fmt_elmnt( 'Expect Action Format', 
                    expect_action_format )
            s = s + "{0:-^79}\"\r\n".format('')
            f.write(s)

    def _set_log_file(self, log_dir, serial_number):
        d   = datetime.date.today()
        timestamp   = d.strftime("%Y%m%d")

        logfile_name    = "{0}.{1}.csv".format(serial_number, timestamp)
        self.log_file   = path.join(log_dir, logfile_name)

if __name__ == "__main__":
    # need to write test unit tests for the Test and Result classes, then use
    # the object generated there to write a unit test for this class.
    pass

