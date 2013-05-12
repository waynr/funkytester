#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

#from dialog import Dialog

import os

##
# @brief Call program in child process, return a tuple containing the exit
# status, everything read from the child's standard output, and standard error
def call_program(arglist, redirect_stdout=False, redirect_stdin=False):

    # rfd = File Descriptor for Reading
    # wfd = File Descriptor for Writing
    child_rfd   = None
    if redirect_stdout:
        (child_rfd, child_wfd) = os.pipe()

    # always return standard error output
    (child_rfd_err, child_wfd_err) = os.pipe()

    child_pid   = os.fork()

    if child_pid == 0:
        os.close(child_rfd_err)
        os.dup2(child_wfd_err, 2)

        if redirect_stdout:
            os.close(child_rfd)
            os.dup2(child_wfd, 1)

        s   = ""
        for each in arglist:
            s = s + " " + each
            
        #print(s)
        os.execv(arglist[0], arglist)

    # parent process
    os.close(child_wfd_err)
    return child_pid, child_rfd_err, child_rfd

