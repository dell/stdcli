# vim:expandtab:autoindent:tabstop=4:shiftwidth=4:filetype=python:tw=0

  #############################################################################
  #
  # Copyright (c) 2005 Dell Computer Corporation
  # Dual Licenced under GNU GPL and OSL
  #
  #############################################################################
"""module

some docs here eventually.
"""

from __future__ import generators

import sys
import time
import subprocess

from trace_decorator import decorate, traceLog, getLog

def clearLine():
    return "\033[2K\033[0G"

def spinner(cycle=['/', '-', '\\', '|']):
    step = cycle[0]
    del cycle[0]
    cycle.append(step)
    # ESC codes for clear line and position cursor at horizontal pos 0
    return step

def pad(strn, pad_width=67):
    # truncate strn to pad_width so spinPrint does not scroll
    if len(strn) > pad_width:
        return strn[:pad_width] + ' ...'
    else:
        return strn

def spinPrint(strn, outFd=sys.stderr):
    outFd.write(clearLine())
    outFd.write("%s\t%s" % (spinner(), pad(strn)))
    outFd.flush()

def timedSpinPrint( strn, start ):
    now = time.time()
    # ESC codes for position cursor at horizontal pos 65
    spinPrint( strn + "\033[65G time: %2.2f" % (now - start) )

@traceLog()
def call_output(cmd, *args, **kargs):
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, *args, **kargs)
    output, err = process.communicate()
    retcode = process.poll()
    if retcode:
        raise CalledProcessError(retcode, cmd, stdout=output, stderr=err)
    return output

