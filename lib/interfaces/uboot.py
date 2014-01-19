#!/usr/bin/env python

# standard libraries
import re, logging, time, os

# installed libraries
import fdpexpect

# local libraries
from serial import SerialInterface, SerialInterfaceError

class UBootTerminalInterface(SerialInterface):

    def __init__(self, prompt="U-Boot>", *args, **kwargs):
        SerialInterface.__init__(self, *args, **kwargs)

        self.ub_env     = dict()
        self.prompt     = prompt

    def __get_env_dict(self,):
        # guard against lack of U-Boot> prompt
        if not self.chk():
            logging.warning("No UBoot prompt found!")
            return False

        test, buf   = self.cmd(
                command = "printenv",
                timeout = 10,
                )

        if test:
            tmp         = self.buf_new
            var_list    = tmp.split('\n')
            for var in var_list:
                match   = re.match(r"^(\w+)=(.*)", var)
                if match:
                    self.ub_env[match.group(1)]   = match.group(2).strip("\r")
        
        return test

    def cmd(self, command, prompt=None, timeout=10):
        if not prompt:
            prompt = self.prompt

        return SerialInterface.cmd(self,
                command = command,
                prompt  = prompt,
                timeout = timeout,
                )
        
    ##
    # @brief Get U-Boot environment variable.
    #
    def get_var(self, varname,):
        self.__get_env_dict()

        ub_env  = self.ub_env

        if varname in ub_env.keys():
            return ub_env[varname]

        return False

    ##
    # @brief Set multiple u-boot environment variables
    #
    def set_var_list(self, varlist):
        for key, value in varlist:
            test, buf   = self.__set_var(key, value)

            if not test:
                debug.error("FAIL: setenv {0} {1}")

        # verify assignment
        self.__get_env_dict()

        missing_assignments = list()
        for key, value in varlist:
            if self.ub_env[key] != value:
                missing_assignments.append((key, value))
            
        if len(missing_assignments) > 0:
            return False, missing_assignments

        return True, None

    ##
    # @brief Set U-Boot environment variable with error check.
    #
    def set_var(self, varname, value):
        test, buf   = self.__set_var(varname, value)

        # verify assignment
        self.__get_env_dict()

        if test: 
            if self.ub_env[varname] == value: 
                return True
            logging.debug("setenv command was successful but the assignment failed!")
            
        logging.debug("'setenv {0}={1}' failed.".format(varname, value))

        return False

    ##
    # @brief Set U-Boot environment variable.
    #
    def __set_var(self, varname, value):
        return self.cmd( 
                command = "setenv {varname} {value}".format(
                    varname = varname,
                    value   = value,
                    ),
                timeout = .5,
                )

    ##
    # @brief Check whether or not the U-Boot prompt is ready.
    #
    # This function will stop U-Boot from booting during the power-up sequence
    # and verify that a "U-Boot>" prompt is available before returning True.
    # Returns false if no "U-Boot>" prompt is available after hitting "Enter".
    #
    def chk(self, timeout=10):

        def debug(result, before, after):
            print("result: " + str(result))
            print("-b-")
            print(m.before)
            print("-a-")
            print(m.after)

        with self.serial.fdpexpect(self.serial.serial_port,
                self.serial.baud_rate) as m:
            try:
                time.sleep(1)
                m.send("\n")
                result = m.expect(["U-Boot>","Autonegotiation timed out"], timeout)
            except fdpexpect.TIMEOUT:
                debug("N/A", m.before, m.after)
                return False
            except fdpexpect.EOF:
                debug("N/A", m.before, m.after)
                return False
    
        if result == 0: # U-Boot>
            return True
        if result == 1: # Autonegotiation timed out
            debug(result, m.before, m.after)
            raise SerialInterfaceError("macb Autonegotiation timed out, please"
                    "check that a CAT5 or compatible Ethernet cable is plugged"
                    "in to the UUT.")

        debug(result, m.before, m.after)
        return False

