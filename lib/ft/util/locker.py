#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

# standard libraries
from functools import wraps
from threading import (
        RLock,
        Condition
        )

## 
# @brief Acquire an object's lock before calling a method, then release it
# after.
#
def acquire_and_release(f, o_type="instance"):

    @wraps(f)
    def wrapper(self, *args, **kwargs):
        if o_type == "instance":
            condition   = self.condition
        else:
            condition   = self.cls_condition

        condition.acquire()
        #print("Condition Lock acquired.")
        result  = f(self, *args, **kwargs)
        condition.release()
        #print("Condition Lock released.")

        return result

    return wrapper

##
# @brief Add a Condition variable to the instance.
#
def add_condition(f):

    @wraps(f)
    def wrapper(self, *args, **kwargs):
        self.rlock      = RLock()
        self.condition  = Condition(self.rlock)
        f(self, *args, **kwargs)

    return wrapper

##
# @brief Implement instance locking for all of an instance's methods.
#
def locker_all(cls):

    # add condition to instance via "__init__"
    setattr(cls, "__init__", add_condition(cls.__init__))

    # decorate all of the class methods
    for key, val in cls.__dict__.items():
        if key.startswith("__") and key.endswith("__") \
                or not callable(val):
                    continue
        setattr(cls, key, acquire_and_release(val, o_type="instance"))

    return cls
    
##
# @brief Implement class locking for all of an instance's methods.
#
def cls_locker_all(cls):

    # add condition to class 
    cls.cls_rlock       = RLock()
    cls.cls_condition   = Condition(cls.cls_rlock)

    # decorate all of the class methods
    for key, val in cls.__dict__.items():
        if key.startswith("__") and key.endswith("__") \
                or not callable(val):
                    continue
        setattr(cls, key, acquire_and_release(val, o_type="class"))
    
    return cls
