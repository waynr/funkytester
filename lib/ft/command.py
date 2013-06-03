#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import logging, threading

import ft.event

class RecipientType:
    PLATFORM = "platform"
    SLOT = "platform_slot"
    UUT = "unit_under_test"
    TEST = "test"
    ACTION = "action"

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
            error = traceback.format_exc()
            self.platform.fire(ft.event.ErrorEvent,
                    obj = self.platform,
                    traceback = error,
                    )
            logging.debug(error)
            return None, error

    def __get_recipient(self, command):
        return self.__get_recipient_v0(command)
        #return self.__get_recipient_v1(command)

    address_index = 2
    ## Get recipient without depending on a specific RecipientType.
    #
    def __get_recipient_v1(self, command):
        def get_object_by_address(tpl):
            parent_address = tpl[0]
            object_index = tpl[1]
            if isinstance(parent_address, tuple):
                parent = get_parent(tpl)
                return parent.get_subordinate(object_index)
            else:
                return platform

        object_address = command[self.address_index]
        try:
            obj = get_object_by_address(object_address)
            return True, obj
        except IndexError, KeyError:
            msg = "ERROR: recipient '{0}:{1}' does not exist".format(
                    recipient_type, recipient_address)
        except Exception:
            import traceback
            msg = traceback.format_exc()
        else:
            msg = "ERROR: invalid recipient type '{0}'".format( recipient_type)

        return False, msg
                
    ## Get recipient by checking the given RecipientType value.
    #
    def __get_recipient_v0(self, command):
        try: 
            recipient_type = command[1]
            recipient_address = command[2]
            if recipient_type == RecipientType.PLATFORM:
                recipient = self.platform
            else:
                recipient_index = recipient_address[1]
                if recipient_type == RecipientType.SLOT:
                    recipient = self.platform.slots[recipient_index]
                elif recipient_type == RecipientType.UUT:
                    recipient = self.platform.uuts[recipient_index]
                elif recipient_type == RecipientType.TEST:
                    uut_index = recipient_address[0][1]
                    recipient = self.platform.uuts[uut_index].\
                            tests[recipient_index]
                elif recipient_type == RecipientType.ACTION:
                    uut_index = recipient_address[0][0][1]
                    test_index = recipient_address[0][1]
                    recipient = self.platform.uuts[uut_index].\
                            tests[test_index].actions[recipient_index]
        except IndexError, KeyError:
            msg = "ERROR: recipient '{0}:{1}' does not exist".format(
                    recipient_type, recipient_address)
        except Exception:
            import traceback
            msg = traceback.format_exc()
        else:
            return True, recipient

        self.platform.fire(ft.event.ErrorEvent,
                obj = self.platform,
                traceback = msg,
                )

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
            error = traceback.format_exc()
            obj.fire(ft.event.ErrorEvent,
                    obj = obj,
                    traceback = error,
                    )
            logging.debug(error)

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
