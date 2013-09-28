#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

# Copyright (C) 2012  Wayne Warren (wwarren@emacinc.com)
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
# 
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51 Franklin
# Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# Note: Much of this file's design is inspired by bitbake version 1.15.3
#

__major_version__ = "00"
__minor_version__ = "05"
__bug_version__ = "00" # need to create a git hook or something that automatically
                     # replaces this text with a short SHA256 hash

__version__ = ".".join([__major_version__, __minor_version__, __bug_version__])

import signal, os, os.path as path
import sys, logging, optparse, socket, time

bindir = path.dirname(__file__)
topdir = path.dirname(bindir)
libdir = path.join(topdir, "lib")
extdir = path.join(topdir, "ext")

sys.path.insert(0, libdir)
sys.path.insert(0, extdir)

#-------------------------------------------------------------------------------
# Configure logging

log_file = path.join(topdir, "pytest_log")
log_level = logging.DEBUG

logging.basicConfig(
        level = log_level,
        format = "%(asctime)s %(threadName)-5s %(levelname)-5s %(module)-5s " + \
                "%(funcName)-5s %(message)s",
                datefmt = '%Y%m%d %H:%M:%S',
        filename = log_file,
        filemode = 'a',
        )

logging.debug("GE Functional Test Init")

#-------------------------------------------------------------------------------
# Load Functional Test & Associated libraries

from ft.platform import Platform 

#-------------------------------------------------------------------------------
# Option Parsing

def parse_options():
    option_parser = optparse.OptionParser(
            version = "FunkyTester, Version {0}".format(
                __version__),
            usage = """%prog [options] <TEST_DIR>""",
            )

    option_parser.add_option("-v", "--verbose", 
            help="Display verbose/debug output during test run.",
            action="store_true", 
            dest="verbose",
        )
    option_parser.add_option("-q", "--quiet", 
            help="Turn off non-UI test output.",
            action="store_false", 
            dest="verbose",
        )
    option_parser.add_option("-d", 
            help="Enable various debug features.",
            action="count", 
            dest="debug",
        )
    option_parser.add_option("", "--profile", 
            help="Produce statistical information about code runtime.",
            action="store_true", 
            dest="profile",
        )
    option_parser.add_option("", "--profile-dir", 
            help="File in which to store profiling statistics.",
            action="store", 
            type="string",
            dest="profile_dir",
        )
    option_parser.add_option("", "--client-only", 
            help="Run the client only; connect to a remote server.",
            action="store_true", 
            dest="client_only",
        )
    option_parser.add_option("", "--server-only", 
            help="Run the server only; connect with a UI client.",
            action="store_true", 
            dest="server_only",
        )
    option_parser.add_option("-f", "--tftp", 
            help="Set the server from which to load TFTP files during test.",
            action="store", 
            type="string", 
            dest="tftp_server_ip",
        )
    option_parser.add_option("-n", "--nfs", 
            help="Set the server which offers the appropriate NFS rootfs.",
            action="store", 
            type="string", 
            dest="nfs_server_ip",
        )
    option_parser.add_option("-m", "--mode", 
            action="store", 
            type="string", 
            dest="test_mode",
        )
    option_parser.add_option("", "--server-type", 
            help="Specify the server type. Default is 'sockets'.",
            action="store", 
            type="string",
            dest="platform_server_type",
        )
    option_parser.add_option("-p", "--port", 
            help="Connect to the specified port. Default is 5932.",
            action="store", 
            type="int",
            dest="platform_server_port",
        )
    option_parser.add_option("-H", "--host", 
            help="Connect to the specified platform server host.",
            action="store", 
            type="string",
            dest="platform_server_host",
        )
    option_parser.add_option("-l", "--log-db", 
            help="Use the specified database connection parameters for log data.",
            action="store", 
            type="string",
            dest="logdb_connection",
        )
    option_parser.add_option("-a", "--platform-manifest", 
            help="Use the specified platform manifest file.",
            action="store", 
            type="string",
            dest="platform_manifest_file",
        )
    
    option_parser.set_defaults(
            tftp_server_ip = "192.168.2.1",
            nfs_server_ip = "192.168.2.1",

            platform_server_host = "localhost",
            platform_server_port = 5932,
            platform_server_type = "sockets",

            logdb_connection = "sqlite:///testlog.db",
    
            config_file = None,
            platform_manifest_file = "./resources/platforms/manifest.yaml",
            test_mode = None,
    
            verbose = False,
            profile = False,
            profile_dir = "profile",
            )

    return option_parser

def setup_platform_server(platform_server, options):
    platform_server.init_server(options)
    platform_server.init_platform(options)
    platform_server.detach()

    if options.server_only:
        print("server address: %s, server port: %s" %
              (platform_server.serverinfo[0],
               platform_server.serverinfo[1]))

def is_server_local(server_info):
    host = server_info[0]
    return host == "localhost" or host.startswith("127")

def init_ui(platform_server, client):
    import ui.funct
    try:
        return platform_server.launch_ui(ui.funct.main, client)
    except Exception:
        import traceback
        traceback.print_exc(15)
    finally:
        client.terminate()

def main():
    option_parser = parse_options()
    (options, args) = option_parser.parse_args()

    options.profile_dir = path.join(topdir, options.profile_dir)

    server_info = (options.platform_server_host, options.platform_server_port)

    if options.profile:
        import cProfile
        pr = cProfile.Profile()
        pr.enable()

    #-------------------
    # Prepare Default Database Engine
    #
    # Need to choose database module dynamically.
    #
    from emac.orm.achievo import setup_default_engine
    setup_default_engine()

    #-------------------
    # Load PlatformServer
    #
    try:
        module = __import__("ft.server", 
                fromlist = [options.platform_server_type] )
        server = getattr(module, options.platform_server_type)
    except AttributeError:
        sys.exit("ERROR: Invalid server type '%s'.\n"
                "Available Servers: process, socket [default]." 
                % options.platform_server_type )

    platform_server = server.PlatformServer()

    if options.platform_server_type == "sockets":
        if options.server_only:
            try:
                setup_platform_server(platform_server, options)
            except socket.error, e:
                if e.errno == 98:
                    sys.exit("ERROR: Address '{0}:{1}' already in use!".format(
                        server_info[0], server_info[1]))
            platform_server.server.join()
        elif options.client_only:
            try:
                client = platform_server.establish_connection(server_info)
                init_ui(platform_server, client)
            except server.PlatformTimeoutError as e:
                sys.exit(e.message)
            except socket.error as msg:
                sys.exit("ERROR: Could not connect to '{0}:{1}.".format(
                    server_info[0], server_info[1]))
        else:
            if not is_server_local(server_info):
                sys.exit("ERROR: '{0}:{1}' is not local!".format(
                    server_info[0], server_info[1]))
            setup_platform_server(platform_server, options)
            try:
                client = platform_server.establish_connection(server_info)
                init_ui(platform_server, client)
            except socket.error as msg:
                sys.exit("ERROR: Could not connect to '{0}:{1}'.".format(
                    server_info[0], server_info[1]))
            platform_server.server.join()
    elif options.platform_server_type == "process":
        setup_platform_server(platform_server, options)
        client = platform_server.establish_connection()
        init_ui(platform_server, client)
    
    if options.profile:
        pr.disable()
        import pstats, io, threading
        t = threading.current_thread()

        try:
            os.makedirs(options.profile_dir)
        except:
            logging.info("Directory already exists: {0}".format(
                options.profile_dir))
        profile_file = path.join(options.profile_dir, t.name)
        f = io.open( profile_file, 'wb')

        ps = pstats.Stats(pr, stream=f)
        ps.sort_stats("file", "cumulative")
        ps.print_stats()

if __name__ == "__main__":
    try:
        ret = main()
    except Exception:
        ret = 1
        import traceback
        traceback.print_exc(15)
    os.kill(os.getpid(), signal.SIGKILL)
    sys.exit(ret)

