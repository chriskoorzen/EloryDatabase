from os import sep, makedirs, name
from os.path import isdir, expanduser


# For Windows Users
USER_DIR = expanduser("~")
DATA_DIR = USER_DIR + sep + "AppData" + sep + "Local" + sep + "Elory"
LOGS_DIR = DATA_DIR + sep + "logs"
CONF_DIR = DATA_DIR + sep + "config"
platform = name


def dependencies_exist():
    return isdir(DATA_DIR)


def setup_dependencies():
    makedirs(DATA_DIR)      # Main App folder
    makedirs(LOGS_DIR)
    makedirs(CONF_DIR)
