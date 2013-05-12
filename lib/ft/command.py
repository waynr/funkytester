#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import logging, threading

import ft.event

class RecipientType:
    PLATFORM = "platform"
    SLOT = "platform_slot"
    UUT = "unit_under_test"
    TEST = "test"
    ACTIONS = "action"

class Command(object):

    ( ADDRESS,
        RECIPIENT_TYPE,
        MESSAGE,
        ) = range(3)

    ( NAME,
        DATA,
        SYNCHRONOUS,
        ) = range(3)

    def __init__(self, platform):
        self.platform = platform

    ## Runs the specified command; depending on how many values are in the
    #  tuple, run the old or the new version of the run_command method.
    #
    #  @param command Currently either a 3- or 5- tuple containing important
    #  command information.
    #
    def run_command(self, command):
        logging.debug(command)
        if len(command) == 3:
            return self.__run_command_v2(command)
        elif len(command) == 5:
            return self.__run_command_v1(command)

    def __run_command_v2(self, command):
        raise NotImplementedError

    def __run_command_v1(self, command):
        command_name = command[0]
        command_is_synchronous = command[4]

        check = self.__get_recipient(command)
        if not check[0]:
            return check
        recipient = check[1]

        try:
            if command_is_synchronous:
                return recipient.run_command(command)
            else:
                cw = CommandWorker(recipient, command)
                cw.start()
        except:
            import traceback
            exc = traceback.format_exc()
            error = "Command {0} failed: {1}".format(command_name, exc)
            return None, error

    def __get_recipient(self, command):
        try: 
            recipient_type = command[1]
            if recipient_type == RecipientType.PLATFORM:
                recipient = self.platform
            else:
                recipient_address = command[2][1]
                if recipient_type == RecipientType.SLOT:
                    recipient = self.platform.slots[recipient_address]
                if recipient_type == RecipientType.UUT:
                    recipient = self.platform.uuts[recipient_address]
            return True, recipient
        except IndexError, KeyError:
            msg = "ERROR: recipient '{0}:{1}' does not exist".format(
                    recipient_type, recipient_address)
        except Exception:
            import traceback
            msg = traceback.format_exc()
        else:
            msg = "ERROR: invalid recipient type '{0}'".format( recipient_type)

        return False, msg

## Desperate attempt to work around a bug in the initial async command stuff.
#
class CommandWorker(threading.Thread):

    def __init__(self, obj, command):
        super(CommandWorker, self).__init__()

        self.obj = obj
        self.command = command

    def run(self):
        obj = self.obj
        obj.lock.acquire()

        command_name = self.command[0]
        command_data = self.command[3]

        try:
            command_method = getattr(obj.CommandsAsync, command_name)
            self.result = command_method(obj, command_data)
        except:
            import traceback
            obj.fire(ft.event.ErrorEvent,
                    obj = obj,
                    traceback = traceback.format_exc()
                    )

        obj.lock.release()

## Mixin designed to synchronize synchronous command behavior for objects that
#  recieve commands. Requires that implementing classes have a reentrant lock
#  attribute named 'lock' and own two classes, CommandsSync and CommandsAsync.
#
class Commandable(object):

    ## Synchronous command form should be the same for all Commandables
    #
    def run_command(self, command):
        self.lock.acquire()
        result = (False, None)

        command_name = command[0]
        command_data = command[3]

        command_method = getattr(self.CommandsSync, command_name)
        result = command_method(self, command_data)

        self.lock.release()
        return result

class CommandError(Exception):
    def __init__(self, command_name):
        self.message = ("Command error: {0}").format(command_name)
    
    def __str__(self):
        return repr(self.message)
