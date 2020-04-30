import os

from replicant.utils import parse_config

CONF_FILE = os.environ.get('REPLICANT_CONFIG', 'replicant/conf.ini')

configuration = parse_config(CONF_FILE)
