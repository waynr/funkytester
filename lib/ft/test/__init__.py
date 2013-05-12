#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

class Status:
    init = "INIT"
    success = "SUCCESS"
    success_invalid_interface = "INVALID_TEST"
    fail = "FAIL"
    broken_test = "BROKEN_TEST"
    unknown = "UNKNOWN"

from specification import *
from action import *
from test import *

__all__ = [
        Specification,
        SpecificationError,
        Test,
        Status,
        Action,
        ]
