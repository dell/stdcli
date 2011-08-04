#!/usr/bin/env python
# vim:expandtab:autoindent:tabstop=4:shiftwidth=4:filetype=python:tw=0

import sys, os, time
from signal import SIGTERM
from stdcli.trace_decorator import traceLog, getLog

class Daemon:
    """
    A generic daemon class.

    Usage: subclass the Daemon class and override the run() method
    """
    @traceLog()
    def __init__(self, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null', foreground=False):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.foreground = foreground

    @traceLog()
    def daemonize(self):
        """
        do the UNIX double-fork magic, see Stevens' "Advanced
        Programming in the UNIX Environment" for details (ISBN 0201563177)
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        """
        try:
            pid = os.fork()
            if pid > 0:
                # exit first parent
                os._exit(0)
        except OSError, e:
            sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
            os._exit(1)

        # decouple from parent environment
        os.chdir("/")
        os.setsid()
        os.umask(0)

        # do second fork
        try:
            pid = os.fork()
            if pid > 0:
                # exit from second parent
                os._exit(0)
        except OSError, e:
            sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
            os._exit(1)

        # redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = file(self.stdin, 'r')
        so = file(self.stdout, 'a+')
        se = file(self.stderr, 'a+', 0)
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

    @traceLog()
    def start(self):
        """
        Start the daemon
        """
        # Start the daemon
        try:
            os.chdir("/") # so that daemon/non-daemon start from same dir
            if not self.foreground:
                self.daemonize()
            self.run()
        except Exception, e:
            import traceback
            traceback.print_exc()

    @traceLog()
    def run(self):
        """
        You should override this method when you subclass Daemon. It will be called after the process has been
        daemonized by start() or restart().
        """
