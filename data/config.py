#!/usr/bin/env python

import argparse
import os.path
import ConfigParser

config = ConfigParser.ConfigParser({
    'database': 'S8',
    'password': 'S8',
    'username': 'S8',
    'host': 'localhost',
    'port': '3306',
    'subscription': 'L8',
    'domains': 'all',
    'level_DEBUG': 'True',
    'level_INFO': 'True',
    'level_NOTICE': 'True',
    'level_WARNING': 'True',
    'level_ERROR': 'True',
    'level_CRITICAL': 'True',
    'level_ALERT': 'True',
    'level_EMERGENCY': 'True',
})

conf_path = os.path.expanduser('~') + '/.t8'

if os.path.isfile(conf_path):
    config.read(conf_path)
else:
    config.add_section('config')

parser = argparse.ArgumentParser(description='Terminal viewer for L8 redis-backed logger.')
parser.add_argument('-v', '--verbose',  default=False, action='store_true')
parser.add_argument('-d', '--database', default=config.get('config', 'database'))
parser.add_argument('-p', '--password', default=config.get('config', 'password'))
parser.add_argument('-u', '--username', default=config.get('config', 'username'))
parser.add_argument('--host', default=config.get('config', 'host'))
parser.add_argument('--port', default=config.get('config', 'port'))
parser.add_argument('--subscription', default=config.get('config', 'subscription'))
parser.add_argument('-s', '--startDate')
parser.add_argument('-e', '--endDate')
parser.add_argument('--eDEBUG', default=config.getboolean('config', 'level_DEBUG'))
parser.add_argument('--eINFO', default=config.getboolean('config', 'level_INFO'))
parser.add_argument('--eNOTICE', default=config.getboolean('config', 'level_NOTICE'))
parser.add_argument('--eWARNING', default=config.getboolean('config', 'level_WARNING'))
parser.add_argument('--eERROR', default=config.getboolean('config', 'level_ERROR'))
parser.add_argument('--eCRITICAL', default=config.getboolean('config', 'level_CRITICAL'))
parser.add_argument('--eALERT', default=config.getboolean('config', 'level_ALERT'))
parser.add_argument('--eEMERGENCY', default=config.getboolean('config', 'level_EMERGENCY'))
parser.add_argument('--domains', default=config.get('config', 'domains'))
parser.add_argument('--method', default='latest', help='Available methods: \n\
list_domains -> show all domains with error count\n\
domain -> show all errors for a domain with counts')

args = parser.parse_args()
