import sys
import os
import os.path
import fnmatch
import functools
import traceback

from org.openhab.core.jsr223.internal.shared import Rule, Openhab
from openhab.globals import oh, StartupTrigger

from org.openhab.core.types import UnDefType
NULL = UnDefType.NULL
UNDEF = UnDefType.UNDEF

# Decorators

def log_traceback(fn):
    functools.wraps(fn)
    def wrapper(*args, **kwargs):
        # noinspection PyBroadException
        try:
            fn(*args, **kwargs)
        except Exception as ex:
            if hasattr(args[0], "log"):
                args[0].log.error(traceback.format_exc())
            else:
                traceback.print_ex()
    return wrapper

def rule(clazz):
    """
    Decorator for adding OH1 Rule functionality to a class.
    """
    clazz = type(clazz.__name__, (clazz, Rule), {})
    def new(cls, *args, **kwargs):
        instance = super(cls, cls).__new__(cls, *args, **kwargs)
        instance.log = Openhab.getLogger(cls.__name__)
        return instance
    clazz.__new__ = staticmethod(new)
    clazz.execute = log_traceback(clazz.execute)
    return clazz

class OpenhabRule(Rule):
    """
    Rule base class that will usually give better stack traces when rule execution fails.
    """
    def __init__(self):
        self.log = Openhab.getLogger(type(self).__name__)

    def execute(self, event):
        try:
            self.safe_execute(event)
        except Exception as ex:
            self.log.error(type(self).__name__ + "\n" + traceback.format_exc())

    # TODO make this not specific to Pushover
    def send_notification(self, message):
        self.log.info("Sending notification: {}", str(message))
        oh.getAction("Pushover").pushover(str(message))

from synchronize import make_synchronized

class StartupCallback(OpenhabRule):
    """
    This is a pseudo-rule that will execute code when the rule engine is started.
    The primary purpose is to defer execution of code that would cause otherwise
    trigger OSGI circular dependencies during the rule engine startup.
    """
    def __init__(self, callback, *args, **kwargs):
        super(StartupCallback, self).__init__()
        self._callback = callback
        self._args = args
        self._kwargs = kwargs
        # StartupTrigger is invoked multiple times (?)
        self._triggered = False
    
    def getEventTrigger(self):
        return [ StartupTrigger() ]
    
    @make_synchronized
    def safe_execute(self, event):
        if not self._triggered:
            self._callback(*self._args, **self._kwargs)
            self._triggered = True

            _openhab_jars = None

def _find_jars():
    # The intention is to locate the directory where the openhab JAR files
    # are located. These may be in different places depending on how openHAB
    # was installed.
    server_dir = os.getenv("OPENHAB_HOME")
    if not server_dir:
        raise Exception("Must specify OPENHAB_HOME environment variable")
    for root, subdirs, files in os.walk(server_dir):
        for f in files:
            if f.endswith(".jar"):
                _openhab_jars.append((f, os.path.join(root, f)))

def import_jar(name_pattern):
    # lazily discover jar locations
    global _openhab_jars
    if _openhab_jars is None:
        _openhab_jars = []
        _find_jars()
    # find the matching jar
    for jar_name, jar_path in _openhab_jars:
        if fnmatch.fnmatch(jar_name, name_pattern):
            sys.path.append(jar_path)
            return
    raise Exception('jar not found: {}'.format(name_pattern))


class SingletonMeta(type):
    """
        Metaclass that attempts to maintain a single instance of a class at any 
        given time (with dispose of the previous instance) when the associated 
        instance is created. This is useful when an object must be disposed when 
        another is created (during reload, for example). It compensates for rules
        not having a teardown callback.
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        """Disposes previous instance when new one is created"""
        if cls.__name__ in cls._instances:
            cls._instances[cls.__name__].dispose()
        instance = super(SingletonMeta, cls).__call__(*args, **kwargs)
        cls._instances[cls.__name__] = instance
        return instance