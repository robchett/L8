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
import time
import re
import base64
import argparse
from bcolors import bcolors
import pymysql as mysql
import pymysql.err as mysql_exceptions

mysql.install_as_MySQLdb()


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
            self.mysql = mysql.connect(args.host, args.username, args.password, args.database)
        except (mysql_exceptions.OperationalError, mysql_exceptions.ProgrammingError) as err:
            sys.stdout.write('%s%s%s%s\n' % (bcolors.FAIL, bcolors.UNDERLINE, "MYSQL error: ", bcolors.ENDC))
            sys.stdout.write('%s%s%s\n' % (bcolors.FAIL, err, bcolors.ENDC))
            sys.exit()

    @staticmethod
    def format_timestamp(ts):
        return time.strftime('%Y-%m-%d', time.gmtime(ts))

    @staticmethod
    def format_datetime(ts):
        return ts.strftime("%Y-%m-%d")

    def get_time_sql(self):
        return 'DATE(time) >= "{0}" AND DATE(time) <= "{1}"'.format(self.format_timestamp(self.start_time), self.format_timestamp(self.end_time))

    def get_level_sql(self):
        return 'level IN ("{0}")'.format('","'.join([self.levels.keys[i] for i in self.error_levels if self.error_levels[i]]))

    def domains(self):
        with self.mysql.cursor() as cursor:
            cursor.execute('SELECT domain, count(*) as count FROM `messages` WHERE {0} AND {1} GROUP BY domain ORDER BY count DESC'.format(
                self.get_time_sql(),
                self.get_level_sql())
            )
            res = []
            while True:
                record = cursor.fetchone()
                if not record:
                    break
                res.append(self.Domain(record[0], record[1]))
            return res

    def errors(self, host, mode):
        with self.mysql.cursor() as cursor:
            if mode == self.mode.totals:
                cursor.execute('SELECT filename, line, message, level, source, context, count(*) as count, time, id, domain FROM `messages` WHERE domain = "{0}" AND {1} AND {2} GROUP BY filename, line ORDER BY count DESC'.format(
                    host,
                    self.get_time_sql(),
                    self.get_level_sql())
                )
            else:
                cursor.execute('SELECT filename, line, message, level, source, context, 1 as count, time, id, domain FROM `messages` WHERE domain = "{0}" AND {1} AND {2} ORDER BY time DESC'.format(
                    host,
                    self.get_time_sql(),
                    self.get_level_sql())
                )
            res = []
            while True:
                record = cursor.fetchone()
                if not record:
                    break
                res.append(self.Error(record[8], record[0], record[1], record[2], record[3], record[4], record[5], record[6], record[7], record[9]))
            return res

    def delete_type(self, error):
        with self.mysql.cursor() as cursor:
            sql = "DELETE FROM messages WHERE line = %s AND filename = %s AND domain = %s"
            parameters = (
                error.line,
                error.file,
                error.domain
            )
            cursor.execute(sql, parameters)
            self.mysql.commit()

    def delete_entry(self, error):
        with self.mysql.cursor() as cursor:
            cursor.execute("DELETE FROM messages WHERE id = %s", error.id)
            self.mysql.commit()

    class mode:
        totals = 1
        latest = 2

    class Domain:
        def __init__(self, host, error_count):
            self.host = host
            self.error_count = error_count
            pass

    class Error:
        def __init__(self, id, file, line, message, level, source, context, count, time, domain):
            self.id = id
            self.time = time
            self.count = count
            self.context = context
            self.source = source
            self.level = level
            self.message = message
            self.line = line
            self.file = file
            self.domain = domain
