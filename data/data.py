#!/usr/bin/env python
"""
D8.py
Static (mysql) log viewer for the L8 redis-backed logger.

Copyright (C) 2014-2015 Alan McFarlane <alan@node86.com>
Copyright (C) 2014-2015 Rob Chett <robchett@gmail.com>
All Rights Reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from this
   software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
"""

import datetime
import json
import math
import redis
import sys
import threading
import _mysql
import _mysql_exceptions
import time
import re
import base64
import argparse
from bcolors import bcolors

class Data:
    
    class levels:
        keys = ['DEBUG', 'INFO', 'NOTICE', 'WARNING', 'ERROR', 'CRITICAL', 'ALERT', 'EMERGENCY']
        DEBUG = 0
        INFO = 1
        NOTICE = 2
        WARNING = 3
        ERROR = 4
        CRITICAL = 5
        ALERT = 6
        EMERGENCY = 7

    def __init__(self, args):
        self.start_time = time.time() - (7 * 24 * 60 * 60)
        self.end_time = time.time() + (24 * 60 * 60)
        self.error_levels = {
            self.levels.DEBUG: 1,
            self.levels.INFO: 1,
            self.levels.NOTICE: 1,
            self.levels.WARNING: 1,
            self.levels.ERROR: 1,
            self.levels.CRITICAL: 1,
            self.levels.ALERT: 1,
            self.levels.EMERGENCY: 1,
        }
        try:
            self.mysql = _mysql.connect(args.host, args.username, args.password, args.database)
        except (_mysql_exceptions.OperationalError, _mysql_exceptions.ProgrammingError) as err:
            sys.stdout.write('%s%s%s%s\n' % (bcolors.FAIL, bcolors.UNDERLINE, "MYSQL error: ", bcolors.ENDC))
            sys.stdout.write('%s%s%s\n' % (bcolors.FAIL, err, bcolors.ENDC))
            sys.exit()

    def format_time(self, ts):
        return time.strftime("%Y-%m-%d", time.gmtime(ts))

    def get_time_sql(self):
        return 'DATE(time) >= "{0}" AND DATE(time) <= "{1}"'.format(self.format_time(self.start_time), self.format_time(self.end_time))

    def get_level_sql(self):
        return 'level IN ("{0}")'.format('","'.join([self.levels.keys[i] for i in self.error_levels if self.error_levels[i]]))


    def domains(self):
        self.mysql.query('SELECT domain, count(*) as count FROM `messages` WHERE {0} AND {1} GROUP BY domain ORDER BY count DESC'.format(self.get_time_sql(), 
        self.get_level_sql()))
        result = self.mysql.use_result()
        res = []
        while True:
            record = result.fetch_row()
            if not record:
                break
            res.append(self.Domain(record[0][0], record[0][1]))
        return res

    def errors(self, host, mode):
        if mode == self.mode.totals:
            self.mysql.query('SELECT filename, line, message, level, source, context, count(*) as count, time FROM `messages` WHERE domain = "{0}" AND {1} AND {2} GROUP BY filename, line ORDER BY count DESC'.format(host, self.get_time_sql(), self.get_level_sql()))
        else:
            self.mysql.query('SELECT filename, line, message, level, source, context, 1 as count, time FROM `messages` WHERE domain = "{0}" AND {1} AND {2} ORDER BY time DESC'.format(host, self.get_time_sql(), self.get_level_sql()))
        result = self.mysql.use_result()
        res = []
        while True:
            record = result.fetch_row()
            if not record:
                break
            res.append(self.Error(record[0][0], record[0][1], record[0][2], record[0][3], record[0][4], record[0][5], record[0][6], record[0][7]))
        return res

    class mode:
        totals = 1
        latest = 2


    class Domain:
        def __init__(self, host, error_count):
            self.host = host
            self.error_count = error_count
            pass

    class Error:
        def __init__(self, file , line, message, level, source, context, count, time):
            self.time = time
            self.count = count
            self.context = context
            self.source = source
            self.level = level
            self.message = message
            self.line = line
            self.file = file


'''

        start_date = ('time >= "' + args.startDate + '"') if args.startDate else ''
        end_date = ('time =< "' + args.endDate + '"') if args.endDate else ''

        date_sql = ' AND '.join([i for i in ['1', start_date, end_date] if i != ''])

        if args.domain is None:


        elif args.method == 'totals':
            mysql.query('SELECT filename, line, message, level, source, context, count(*) as count FROM `messages` WHERE ' + date_sql + ' AND domain = "' + args.domain + '" GROUP BY filename, line ORDER BY count DESC')
            result = mysql.use_result()
            sys.stdout.write('%s %-50s %-50s %-10s %-10s %-10s %-10s %s\n' % (
                bcolors.UNDERLINE, ' ', ' ', '', '', '', '', bcolors.ENDC))
            sys.stdout.write('%s|%-50s|%-50s|%-10s|%-10s|%-10s|%-10s|%s\n' % (
                bcolors.UNDERLINE, 'File:Line', 'Message', 'Level', 'Source', 'Context', 'Count', bcolors.ENDC))
            while True:
                record = result.fetch_row()
                if not record:
                    break
                sys.stdout.write('|%-44s:%-5s|%-50s|%-10s|%-10s|%-10s|%-10s|\n' % (
                    record[0][0], record[0][1], record[0][2], record[0][3], record[0][4],
                    base64.b64decode(record[0][5]),
                    record[0][6]))
        elif args.method == 'latest':
            mysql.query(
                'SELECT filename, line, message, level, source, context FROM `messages` WHERE ' + date_sql + ' AND domain = "' + args.domain + '" ORDER BY time DESC')
            result = mysql.use_result()
            sys.stdout.write('%s %-50s %-50s %-10s %-10s %-10s %s\n' % (
                bcolors.UNDERLINE, ' ', ' ', '', '', '', bcolors.ENDC))
            sys.stdout.write('%s|%-50s|%-50s|%-10s|%-10s|%-10s|%s\n' % (
                bcolors.UNDERLINE, 'File:Line', 'Message', 'Level', 'Source', 'Context', bcolors.ENDC))
            while True:
                record = result.fetch_row()
                if not record:
                    break
                sys.stdout.write('|%-44s:%-5s|%-50s|%-10s|%-10s|%-10s|\n' % (
                    record[0][0], record[0][1], record[0][2], record[0][3], record[0][4],
                    base64.b64decode(record[0][5])))
            pass

"""
TODO
----
Need to be able to filter for event severity and/or event contents
"""
'''
