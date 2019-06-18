import os
import configparser


config = configparser.ConfigParser()
config_file = os.path.expanduser('~/.ecstools')
config_file_local = os.path.realpath('.ecstools')
config.read([config_file, config_file_local])
