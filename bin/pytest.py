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

__version__ = "0.3.0"

import signal, os, os.path as path
import sys, logging, optparse

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
        format = "%(asctime)s %(name)-5s %(levelname)-5s %(module)-5s " + \
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
# Load Functional Test UI
import ui.funct

def parse_options():
    option_parser = optparse.OptionParser(
            version = "EMAC Functional Test, verison {0}".format(
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
            help="Specify the server type. Default is 'local'.",
            action="store", 
            type="string",
            dest="platform_server_type",
        )
    option_parser.add_option("-s", "--server", 
            help="Connect to the specified platform server, <host>:<port>",
            action="store", 
            type="string",
            dest="platform_server",
        )
    option_parser.add_option("-l", "--log-db", 
            help="Use the specified database connection parameters for log data.",
            action="store", 
            type="string",
            dest="logdb_connection",
        )
    
    option_parser.set_defaults(
            tftp_server_ip = "192.168.2.1",
            nfs_server_ip = "192.168.2.1",

            platform_server = "localhost:5932",
            platform_server_type = "local",

            logdb_connection = "sqlite:///testlog.db",
    
            config_file = None,
            platform_manifest_file = "./resources/platforms/manifest.yaml",
            test_mode = None,
    
            verbose = False,
            )

    return option_parser

def main():
    option_parser = parse_options()
    (options, args) = option_parser.parse_args()

    #-------------------
    # Load PlatformServer
    #
    try:
        module = __import__("ft.server", 
                fromlist = [options.platform_server_type] )
        server = getattr(module, options.platform_server_type)
    except AttributeError:
        sys.exit("ERROR: Invalid server type '%s'.\n"
                "Available Servers: local [default]." 
                % options.platform_server_type )

    #-------------------
    # Prepare Default Database Engine
    #
    # Need to choose database module dynamically as with platformserver
    #
    from achievo import setup_default_engine
    setup_default_engine()

    #-------------------
    # Intialize and detach PlatformServer
    #
    platform_server = server.PlatformServer()
    platform_server.init_server()
    platform_server.init_platform(options.platform_manifest_file)
    platform_server.detach()

    #-------------------
    # Connect to server and Launch UI
    #
    if not options.server_only:
        platform_connection = platform_server.establish_connection()

        try:
            return platform_server.launch_ui(ui.funct.main, platform_connection)
        except Exception:
            import traceback
            traceback.print_exc(15)
        finally:
            platform_connection.terminate()
            platform_server.terminate()
    else:
        print("server address: %s, server port: %s" % (platform_server.serverinfo.host,
            platform_server.serverinfo.port))

if __name__ == "__main__":
    try:
        ret = main()
    except Exception:
        ret = 1
        import traceback
        traceback.print_exc(15)
    os.kill(os.getpid(), signal.SIGKILL)
    sys.exit(ret)

