import os
import configparser


config = configparser.ConfigParser()
config_file = os.path.expanduser('~/.ecstools')
config.read(config_file)
