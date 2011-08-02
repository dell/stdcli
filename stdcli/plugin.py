from trace_decorator import traceLog, getLog
import pkg_resources
moduleVerboseLog = getLog(prefix="verbose.")

class PluginExit(Exception): pass

class Plugin(object): 
    def finishedCliParsing(self, *args, **kargs):
        pass


class PluginContainer(object):
    def __init__(self, disable):
        self.disable = disable
        self.plugins = {}

    @traceLog()
    def loadPlugins(self, plugin_type):
        for entrypoint in pkg_resources.iter_entry_points(plugin_type):
            skip=0
            for excludepat in self.disable:
                    if fnmatch.fnmatch(entrypoint.name, excludepat):
                        skip=1
                        break
            if not skip:
                moduleVerboseLog.info("loading plugin: %s" % (entrypoint.name,))
                plugin = entrypoint.load()
                plugin_set = self.plugins.get(plugin_type, {})
                plugin_set[entrypoint.name] = plugin
                self.plugins[plugin_type] = plugin_set


    @traceLog()
    def eachPlugin(self, plugin_type):
        for plugin in self.plugins[plugin_type].values():
            yield plugin

    @traceLog()
    def instantiatePlugins(self, plugin_type, *args, **kargs):
        instantiated_type = plugin_type + "_instantiated"
        for name, plugin in self.plugins[plugin_type].items():
                plugin_set = self.plugins.get(instantiated_type, {})
                plugin_set[name] = plugin(*args, **kargs)
                self.plugins[instantiated_type] = plugin_set

    @traceLog()
    def eachInstantiatedPlugin(self, plugin_type):
        instantiated_type = plugin_type + "_instantiated"
        for plugin in self.plugins[instantiated_type].values():
            yield plugin

