# openHAB Jython Utilities

This repository contains [Jython](http://www.jython.org) code for use the [openHAB](http://www.openhab.org) [1.8.x](https://github.com/openhab/openhab/tree/1.8). This is primarily for my own use but I'm making it available to others in case they find it useful.

## Prerequisites

To use this code, you must have installed the openHAB [JSR223 addon](https://github.com/openhab/openhab/wiki/Jsr223-Script-Engine) for use with Jython.

## Installation

There are a couple options for setting up openHAB to use these Jython utilities. You can add `-Dpython.path=<library directory>` to the JVM arguments in your startup script or you can copy (or link) the openhab module directory to a `configurations/script/openhab` subdirectory.

## Utilities

### Rule Decorators

The `openhab.rule` decorator provides extra functionality for Jython-based rules. It adds a `log` attribute to rule instance that references a logger configured with the rule name. It also wraps the execute method to log a traceback of exceptions thrown in the method. This usually provides better information than the default Jython behavior (for excample, it shows the line number of the Jython script where the exception was thrown). When using the decorator, it is not necessary to derive your class from the openHAB `Rule` class (it implements the interface automatically). For example, the following rule shows a normal Jython rule.

```python
class ExampleRule(Rule):
  def getEventTrigger(self):
    return [ StartupTrigger() ]
    
  def execute(self, event):
    oh.logInfo("ExampleRule", str(event))
```

With the rule decorator, it becomes:

```python
import openhab

@openhab.rule
class ExampleRule(object):
  def getEventTrigger(self):
    return [ StartupTrigger() ]
    
  # automatically enhanced with traceback logging
  def execute(self, event):
    self.log.info(str(event))
```
    
### Access to openHAB Configuration
```
import openhab.config
```

This module allows read access to the openhab configuration. This can be useful if you write bindings in Jython and want to include the configuration in the openhab.cfg file.

The `openhab.config.get_config(pid)` function will return a dictionary with the configuration for the given "pid". The "pid" is the identifier at the beginning of a configuration item (e.g., "mycode:foo=5" where "mycode" is the pid).

### Date conversions

openHAB uses both Java and Joda date and time classes. Furthermore, there are Python-specific datetime classes. This module provides conversion functions for translating between the different classes.

```
import openhab.date
```

The conversion functions are:

```
openhab.date.to_python_datetime
openhab.date.to_java_calendar
openhab.date.to_joda_datetime
```

### Quartz scheduler utilities

The openHAB timers are implemented with the [Quartz scheduling framework](http://www.quartz-scheduler.org/). This module provides some utilities that can be useful for debugging and timer management.

```
import openhab.quartz
```

```
# Get the default scheduler
openhab.quartz.get_scheduler()

# Writes information about current Quartz scheduled jobs to the openHAB log file
openhab.quartz.log_jobs()
```

### Jython binding support

Experimental support for defining full openHAB bindings with Jython. More details to come...
