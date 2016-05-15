"""
This is an experimental module intended to support the development of OH1 bindings
using Jython.
"""
from collections import defaultdict

from openhab import SingletonMeta
from openhab.globals import oh
import openhab.quartz

from java.util import Hashtable
from org.osgi.framework import FrameworkUtil
from org.osgi.service.event import EventHandler, EventConstants, EventAdmin
from org.osgi.util.tracker import ServiceTracker

from org.osgi.service.cm import ManagedService
from org.osgi.framework import Constants

# Note: These imports will trigger OSGI dependency resolution
# and have side-effects that cause NPEs in the JSR223 binding.
from org.openhab.core.events import AbstractEventSubscriber
from org.openhab.core.jsr223.internal.engine import Jsr223Engine
from org.openhab.model.item.binding import BindingConfigReader
# ---------------

bundle_context = FrameworkUtil.getBundle(Jsr223Engine).getBundleContext()

def hashtable(*key_values):
    """
    :param key_values: 2-tuples of (key, value)
    :return: initialized Hashtable
    """
    ht = Hashtable()
    for k, v in key_values:
        ht.put(k, v)
    return ht

class Binding(AbstractEventSubscriber, BindingConfigReader, ManagedService):
    """
        Base class for Jython Binding implementations.
    """
    __metaclass__ = SingletonMeta

    def __init__(self, binding_type):
        """
        :param binding_type: the key for the binding, used in item binding strings.
            Also called the service.pid.
        """
        self.log = oh.getLogger(type(self).__name__)
        self._binding_configs = defaultdict(list) # context -> [bindings]
        self._binding_type = binding_type
        self._registrations = []
        self._registrations.append(bundle_context.registerService(
            EventHandler, self, hashtable((EventConstants.EVENT_TOPIC, ["openhab/*"]))))
        self._registrations.append(bundle_context.registerService(
            ManagedService, self, hashtable((Constants.SERVICE_PID, "org.openhab." + binding_type))))
        self._registrations.append(
            bundle_context.registerService(BindingConfigReader, self, hashtable()))
        self._polling_job_key = None
        
    # override
    def getBindingType(self):
        return self._binding_type

    # override
    def validateItemType(self, item, bindingConfig):
        pass

    # override
    def processBindingConfiguration(self, context, item, bindingConfig):
        raise AttributeError("Must override processBindingConfiguration")

    def addBindingConfiguration(self, context, bindingConfig):
        self._binding_configs[context].append(bindingConfig)
        
    # override
    def removeConfigurations(self, context):
        if context in self._binding_configs:
            self.log.debug("{}.removeConfigurations({})".format(self, context))
            del(self._binding_configs[context])

    def findBindingConfiguration(self, predicate):
        try:
            return next(self.findBindingConfigurations(predicate))
        except StopIteration:
            return None

    def findBindingConfigurations(self, predicate):
        for cfgs in self._binding_configs.values():
            for cfg in cfgs:
                if predicate(cfg):
                    yield cfg
                
    # override
    def receiveCommand(self, item_name, command):
        pass

    # override
    def receiveUpdate(self, item_name, state):
        pass

    # override
    def updated(self, dictionary):
        pass

    def poll(self):
        pass
    
    def start_polling(self, period_millis):
        self._polling_job_key = openhab.quartz.schedule_periodic_callback(self.poll, period_millis)

    def stop_polling(self):
        if self._polling_job_key:
            openhab.quartz.get_scheduler().deleteJob(self._polling_job_key)
            self._polling_job_key = None

    def dispose(self):
        for registration in self._registrations:
            registration.unregister()
        self._registrations = []
        self.stop_polling()


class BindingWrapper(Binding):
    """Wraps a binding implementation. The goal is to remove OSGI dependencies in
        the binding implementation for easier testing."""

    def __init__(self, id, target):
        self.target = target
        super(BindingWrapper, self).__init__(id)

    # override
    def validateItemType(self, item, bindingConfig):
        if hasattr(self.target, 'validateItemType'):
            self.target.validateItemType(item, bindingConfig)

    # override
    def processBindingConfiguration(self, context, item, bindingConfig):
        self.target.processBindingConfiguration(context, item, bindingConfig)

    # TODO remove this, have binding manage configs
    def addBindingConfiguration(self, context, bindingConfig):
        self._binding_configs[context].append(bindingConfig)

    # override
    # TODO use stub implementation, have binding manage configs
    def removeConfigurations(self, context):
        if context in self._binding_configs:
            self.log.debug("{}.removeConfigurations({})".format(self, context))
            del(self._binding_configs[context])

    # TODO remove this, have binding manage configs
    def findBindingConfiguration(self, predicate):
        try:
            return next(self.findBindingConfigurations(predicate))
        except StopIteration:
            return None

    # TODO remove this, have binding manage configs
    def findBindingConfigurations(self, predicate):
        for cfgs in self._binding_configs.values():
            for cfg in cfgs:
                if predicate(cfg):
                    yield cfg

    # override
    def receiveCommand(self, item_name, command):
       if hasattr(self.target, 'receiveCommand'):
            self.target.receiveCommand(item_name, command)

    # override
    def receiveUpdate(self, item_name, state):
       if hasattr(self.target, 'receiveUpdate'):
            self.target.receiveCommand(item_name, state)

    # override
    def updated(self, dictionary):
       if hasattr(self.target, 'updated'):
            self.target.updated(dictionary)

    def poll(self):
       if hasattr(self.target, 'poll'):
            self.target.poll()

    def start_polling(self, period_millis):
        self._polling_job_key = openhab.quartz.schedule_periodic_callback(self.poll, period_millis)

    def stop_polling(self):
        if self._polling_job_key:
            openhab.quartz.get_scheduler().deleteJob(self._polling_job_key)
            self._polling_job_key = None

    def dispose(self):
        for registration in self._registrations:
            registration.unregister()
        self._registrations = []
        self.stop_polling()
        if hasattr(self.target, 'dispose'):
            self.target.dispose()

