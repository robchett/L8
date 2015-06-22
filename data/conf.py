#!/usr/bin/env python

import argparse
import os.path
import ConfigParser

config = ConfigParser.ConfigParser({
        'database': 'S8',
        'password': 'S8',
        'username': 'S8',
        'host'    : 'localhost',
        'port'    : '3306',
        })

conf_path = os.path.expanduser('~') + '/.t8'

if os.path.isfile(conf_path):
    config.read(conf_path)
else:
    config.add_section('config')

parser = argparse.ArgumentParser(description='Terminal viewer for L8 redis-backed logger.')
parser.add_argument('-d', '--database', default=config.get('config','database'))
parser.add_argument('-p', '--password', default=config.get('config','password'))
parser.add_argument('-u', '--username', default=config.get('config','username'))
parser.add_argument('--host', default=config.get('config','host'))
parser.add_argument('--port', default=config.get('config','port'))
parser.add_argument('-s', '--startDate')
parser.add_argument('-e', '--endDate')
parser.add_argument('--domain')
parser.add_argument('--method', default='latest', help='Available methods: \n\
list_domains -> show all domains with error count\n\
domain -> show all errors for a domain with counts')

args = parser.parse_args()
