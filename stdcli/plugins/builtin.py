from stdcli.trace_decorator import traceLog, getLog
import pkg_resources

moduleLog = getLog()
moduleVerboseLog = getLog(prefix="verbose.")
moduleDebugLog = getLog(prefix="debug.")
moduleDebugLog.debug("initializing plugin module: %s" % __name__)

from stdcli.plugin import Plugin

class DumpConfigPlugin(Plugin):
    @traceLog()
    def __init__(self, ctx):
        moduleDebugLog.debug("initializing plugin: %s" % self.__class__.__name__)

        # subparser for dumping config (note this is what plugins should do)
        dump_p = ctx.subparsers.add_parser("dump-config", help="Dumps the current config for debug purposes")
        dump_p.set_defaults(func=self.dumpConfigImpl)

    @traceLog()
    def dumpConfigImpl(self, ctx):
        nonconfig=["uid", "func"]
        transforms = {
            "config_files": lambda x: ",".join(x),
            "disabled_plugins": lambda x: ",".join(x),
            "lockfile": lambda x: x or ''
            }
        def trans(t, i):
            return transforms.get(t, lambda x: x)(i)

        print "[general]"
        for i in vars(ctx.args):
            if i in nonconfig: continue
            print "%s: %s" % (i, trans(i, getattr(ctx.args, i)) )

        print
        print "[non-config-items]"
        for i in nonconfig:
            print "%s: %s" % (i, trans(i, getattr(ctx.args, i)) )

        print
        dist_items = ["version", "egg_name", "project_name", "py_version", "location", "requires"]
        transforms = { "egg_name": lambda x: x(), "requires": lambda x: x() }
        import stdcli.cli_main
        dist = pkg_resources.get_distribution(stdcli.cli_main.moduleName)
        print "[egg-info]"
        for i in dist_items:
            print "%s: %s" % (i, trans(i, getattr(dist, i)) )

        print


class SamplePlugin(Plugin):
    @traceLog()
    def __init__(self, ctx):
        moduleDebugLog.debug("initializing plugin: %s" % self.__class__.__name__)

        # adds a separate parser with subcommands for our plugin. 
        # for this sample, the command is called "samplecmd", and the "--test1" and "--test2"
        # arguments are only ever valid after samplecmd has been specified.
        sample_p = ctx.subparsers.add_parser("samplecmd", help="Demo subcmd for sample purposes")
        sample_p.add_argument("--test1", action="store_true", default=False)
        sample_p.add_argument("--test2", action="store_true", default=False)

        # here is how we tell the framework which function to call when 'samplecmd' is specified
        # on the command line
        sample_p.set_defaults(func=self.sampleImpl)


    @traceLog()
    def sampleImpl(self, ctx):
        moduleLog.info("Called sampleImpl()")
        
