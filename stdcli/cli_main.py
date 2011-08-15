# vim:expandtab:autoindent:tabstop=4:shiftwidth=4:filetype=python:tw=0

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# Copyright (C) 2008 Dell Inc.
#  by Michael Brown <Michael_E_Brown@dell.com>
#


"""
Command line interface class and related.
"""

import os
import sys
import time
import fcntl
import signal
import locale
import logging
import logging.config
import argparse
import ConfigParser
import pkg_resources

from trace_decorator import traceLog, getLog
import plugin


import stdcli
_ = stdcli._

__VERSION__=None  # needs to be overridden by individual modules
moduleName=None   # needs to be overridden by individual modules

moduleLog = getLog()
moduleVerboseLog = getLog(prefix="verbose.")

class LockError(Exception): pass
class CliError(Exception): pass

def path_expand(x):
    if x is not None:
        return os.path.realpath( os.path.expandvars( os.path.expanduser( x )))

# only use this function prior to logging availability
def exFatal(message):
    print >> sys.stderr, message
    sys.exit(1)

def sigquit(signum, frame):
    """ SIGQUIT handler for the cli. """
    exFatal(_("QUIT signal caught - exiting immediately"))

def sigterm(signum, frame):
    """ SIGQUIT handler for the cli. """
    moduleLog.info(_("TERM signal caught - exiting immediately"))
    sys.exit()

# for python trace support
def setDebug(*args, **kargs):
    import pdb
    pdb.set_trace()

def main():
    # enable python tracing support
    signal.signal(signal.SIGUSR1,setDebug)

    # handle sigquit early on
    signal.signal(signal.SIGQUIT, sigquit)
    signal.signal(signal.SIGTERM, sigterm)

    try:
        locale.setlocale(locale.LC_ALL, '')
    except locale.Error, e:
        # default to C locale if we get a failure.
        print >> sys.stderr, 'Failed to set locale, defaulting to C'
        locale.setlocale(locale.LC_ALL, 'C')

    # do our cli parsing and config file setup
    # also sanity check the things being passed on the cli
    try:
        # no logging before this returns.
        ctx = BaseContext(prog=os.path.basename(sys.argv[0]), args=sys.argv[1:])
    except (SystemExit,), e:
        raise
    except Exception, e:
        # for debugging only, comment out for release
        import traceback
        traceback.print_exc()
        # no logging at this point yet
        exFatal(str(e))

    ctx.retcode = 0
    try:
        ctx.doCommands()
        moduleVerboseLog.info(_('Complete!'))
    except KeyboardInterrupt:
        moduleLog.critical(_('Exiting on user <CTRL>-C keypress'))
        if ctx.retcode == 0:
            ctx.retcode = 1
    except (Exception,), e:
        if ctx.retcode == 0:
            ctx.retcode = 1

    sys.exit(ctx.retcode)


def setArgDefaults(namespace, conf, args_from_config):
    for argname, argDefault, section, option, transfunc in args_from_config:
        if option is None: option = argname
        setattr(namespace, argname, argDefault)
        if conf.has_section(section):
            if conf.has_option(section, option):
                try:
                    setattr(namespace, argname, transfunc(conf.get(section, option)))
                except (Exception,), e:
                    exFatal(configParseError % {"section": section, "option": option, "value": conf.get(section, option), "error": str(e)})
                continue


class BaseContext(object):
    def __init__(self,prog=moduleName, args=[]):
        configfile = pkg_resources.resource_filename(moduleName,"%s.ini" % moduleName)

        # default cli namespace and program defaults
        self.args = argparse.Namespace()
        self.args.config_files = [configfile,]
        self.args.uid = os.geteuid()

        # setup argument parser and config files
        base_parser = argparse.ArgumentParser(add_help=False)
        self.conf = ConfigParser.ConfigParser()

        # base config options that we have to parse first, related to config files
        base_parser.add_argument("--no-default-config", dest="config_files", action="store_const", const=[], help=_("Dont read default config files."))
        base_parser.add_argument("-c", "--config", dest="config_files", action="append", default=None, metavar="FILENAME", help=_("Add additional config to read."))
        base_parser.add_argument('--version', action='version', version='%(prog)s ' + __VERSION__)
        self.args, remaining_args = base_parser.parse_known_args(args, namespace=self.args)

        # actually read all the config file specified
        self.conf.read(self.args.config_files)

        # argument parse.  command line overrides config file which overrides built-in default
        args_from_config = [
            # argname, default, config file section, config file option, transform
            ("verbosity", 1, "general", None, lambda x: int(x)),
            ("trace", False, "general", None, lambda x: bool(int(x))),
            ("lockfile", None, "general", None, path_expand,),
            ("disabled_plugins", [], "general", None, lambda x: [y.strip() for y in x.split(",") if y.strip()]),
            ("skip_import_errors", False, "general", None, lambda x: bool(int(x))),
            ]

        setArgDefaults(self.args, self.conf, args_from_config)

        # more CLI parsing
        self.parser = p = argparse.ArgumentParser(add_help=False, parents=[base_parser])
        p.add_argument("-v", "--verbose", action="count", dest="verbosity", help=_("Display more verbose output."))
        p.add_argument("-q", "--quiet", action="store_const", const=0, dest="verbosity", help=_("Minimize program output. Only errors and warnings are displayed."))
        p.add_argument("--trace", action="store_true", dest="trace", help=_("Enable verbose function tracing."))
        p.add_argument("--trace-off", action="store_false", dest="trace", help=_("Disable verbose function tracing."))
        p.add_argument("--lockfile", action="store", dest="lockfile", help=_("Specify the lock file."))
        p.add_argument("--reset-disabled-plugin-list", action="store_const", const=[], dest="disabled_plugins", metavar="PLUGIN_NAME_GLOB", help=_("Disable single named plugin."))
        p.add_argument("--disable-plugin", action="append", dest="disabled_plugins", metavar="PLUGIN_NAME_GLOB", help=_("Disable single named plugin."))
        p.add_argument("--skip-import-errors", action="store_true", dest="skip_import_errors", help=_("Disable plugins with module load errors."))
        self.args, remaining_args = p.parse_known_args(args, namespace=self.args)

        self.args.lockfile = path_expand(self.args.lockfile)

        self.setupLogging(configFile=self.args.config_files, verbosity=self.args.verbosity, trace=self.args.trace)

        # parent subparsers for plugins to add cmds to
        self.subparsers = p.add_subparsers(help="%s commands" % moduleName, dest="command_name")

        self.plugins = plugin.PluginContainer(disable=self.args.disabled_plugins, skip_import_errors=self.args.skip_import_errors)
        self.plugins.loadPlugins("%s_cli_extensions" % moduleName)
        self.plugins.instantiatePlugins("%s_cli_extensions" % moduleName, self)

        # final cli parsing. make new parser so we have a --help option. we dont want --help eaten too early or user
        # wont get full CLI help
        self.final_parser = argparse.ArgumentParser(parents=[self.parser])
        self.final_parser.parse_args(remaining_args, namespace=self.args)

        for p in self.plugins.eachInstantiatedPlugin("%s_cli_extensions" % moduleName): p.finishedCliParsing(self)

    def setupLogging(self, configFile, verbosity=1, trace=0):
        # set up logging
        try:
            logging.config.fileConfig(configFile)
        except (ConfigParser.NoSectionError,), e:
            # manually set up basic logging if not present in cfg file
            root_log = logging.getLogger()
            root_log.setLevel(logging.NOTSET)
            hdlr = logging.StreamHandler(sys.stderr)
            hdlr.setLevel(logging.INFO)
            formatter = logging.Formatter('%(message)s')
            hdlr.setFormatter(formatter)
            root_log.addHandler(hdlr)

        root_log        = logging.getLogger()
        module_log         = logging.getLogger(moduleName)
        module_verbose_log = logging.getLogger("verbose")
        module_trace_log   = logging.getLogger("trace")

        module_log.propagate = 0
        module_trace_log.propagate = 0
        module_verbose_log.propagate = 0

        if verbosity >= 1:
            module_log.propagate = 1
        if verbosity >= 2:
            module_verbose_log.propagate = 1
        if verbosity >= 3:
            for hdlr in root_log.handlers:
                hdlr.setLevel(logging.DEBUG)
        if trace:
            module_trace_log.propagate = 1


    @traceLog()
    def lock(self):
        if self.args.lockfile is None:
            return
        self.runLock = open(self.args.lockfile, "a+")
        try:
            fcntl.lockf(self.runLock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.runLock.truncate()
            self.runLock.write("%s" % os.getpid())
            self.runLock.flush()
        except IOError, e:
            runningPid = self.runLock.readline()
            self.runLock.close()
            raise LockError, _("Unable to obtain exclusive lock. Locked by PID: %s." % runningPid)


    @traceLog()
    def unlock(self):
        if self.args.lockfile is None:
            return
        try:
            os.unlink(self.args.lockfile)
            fcntl.lockf(self.runLock.fileno(), fcntl.LOCK_UN)
        except (OSError,), e:
            if e.errno == 2:
                pass # file not found
            else:
                raise

    @traceLog()
    def still_locked(self):
        if self.args.lockfile is None:
            return True
        if os.path.exists(self.args.lockfile):
            return True

    @traceLog()
    def kill(self, sig=signal.SIGTERM):
        if self.args.lockfile is None:
            return

        try:
            self.runLock = open(self.args.lockfile, "r")
        except IOError, e:
            if e.errno == 2:
                moduleLog.info(_("Not currently running."))
            else:
                raise
            return

        runningPid = int(self.runLock.readline().strip())
        try:
            os.kill(runningPid, sig)
        except OSError, e:
            if e.errno == 3:
                moduleLog.info(_("PID %s not running") % runningPid)
            else:
                raise
            return


    @traceLog()
    def doLockLoop(self):
        # loop until we acquire runtime lock
        # print helpful error message with PID of lock holder if we dont get it
        lockerr = ""
        while True:
            try:
                self.lock()
            except LockError, e:
                if str(e) != lockerr:
                    lockerr = str(e)
                    moduleLog.critical(lockerr)
                moduleLog.critical(_("Another app is currently holding the lock; waiting for it to exit..."))
                time.sleep(2)
            else:
                break


    @traceLog()
    def doCommands(self, *args):
        self.args.func(self)

####################################################################
# misc strings
####################################################################


configParseError = _(
"""Problem parsing config file.
    Section [%(section)s] option '%(option)s' was invalid: %(value)s
    Error was: %(error)s""")

