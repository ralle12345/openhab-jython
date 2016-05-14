"""
Utilities for accessing the openHAB configuration file.
"""
import os.path
import re

# if "server/plugins/org.openhab.config.core_1.7.1.jar" not in sys.path:
#     sys.path.append("server/plugins/org.openhab.config.core_1.7.1.jar")

from org.openhab.config.core import ConfigConstants
from java.lang import System

def get_config_file_path():
    return System.getProperty(
        ConfigConstants.CONFIG_FILE_PROG_ARGUMENT,
        os.path.join(
            System.getProperty(
                ConfigConstants.CONFIG_DIR_PROG_ARGUMENT, 
                ConfigConstants.MAIN_CONFIG_FOLDER),
            ConfigConstants.MAIN_CONFIG_FILENAME))

def config_entries(fp):
    for line in fp:
        if line.startswith("#"):
            continue
        matches = re.match("(.*?):(.*?)=(.*)", line.rstrip())
        if matches:
            yield map(lambda x: x.strip(), matches.groups())

def get_config(pid):
    config = {}
    with open(get_config_file_path(), "r") as fp:
        for entry in config_entries(fp):
            if entry[0] == pid:
               config[entry[1]] = entry[2]
    return config
