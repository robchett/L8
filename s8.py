#!/usr/bin/env python
"""
S8.py
Static (mysql) log for the L8 redis-backed logger.

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
from data.bcolors import bcolors

parser = argparse.ArgumentParser(description='Static (mysql) log for the L8 redis-backed logger.')
parser.add_argument('-s', '--subscription', default='L8')
parser.add_argument('-d', '--database', default='S8')
parser.add_argument('-p', '--password', default='S8')
parser.add_argument('-u', '--username', default='S8')
parser.add_argument('--host', default='localhost')
parser.add_argument('--port', default='3306')
parser.add_argument('--domains', default='all', help='Domains to filter out, defaults to "all"')
args = parser.parse_args()


class Consumer(threading.Thread):
    def __init__(self, r, channels, domains):
        threading.Thread.__init__(self)
        self.redis = r
        self.pubsub = self.redis.pubsub()
        self.pubsub.subscribe(channels)
        self.map = ['DEBUG', 'INFO', 'NOTICE', 'WARNING', 'ERROR', 'CRITICAL', 'ALERT', 'EMERGENCY']
        self.domains = domains
        self.connect()

    def connect(self):
        try:
            self.mysql = _mysql.connect(args.host, args.username, args.password, args.database)
            self.mysql.query('SELECT * FROM `messages` LIMIT 1')
            result = self.mysql.use_result()
        except (_mysql_exceptions.OperationalError, _mysql_exceptions.ProgrammingError) as err:
            sys.stdout.write('%s%s%s%s\n' % (bcolors.FAIL, bcolors.UNDERLINE, "MYSQL error: ", bcolors.ENDC))
            sys.stdout.write('%s%s%s\n' % (bcolors.FAIL, err, bcolors.ENDC))
            sys.stdout.write('%sCREATE DATABASE %s;%s\n' % (bcolors.WARNING, args.database, bcolors.ENDC))
            sys.stdout.write('%s\
CREATE TABLE `messages` (\n\
  `id` int(11) NOT NULL AUTO_INCREMENT,\n\
  `domain` varchar(255) DEFAULT NULL,\n\
  `time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,\n\
  `level` enum("DEBUG","INFO","NOTICE","WARNING","ERROR","CRITICAL","ALERT","EMERGENCY") DEFAULT NULL,\n\
  `source` enum("STATEMENT","ERROR","EXCEPTION") DEFAULT NULL,\n\
  `message` text,\n\
  `filename` varchar(255) DEFAULT NULL,\n\
  `line` int(10) DEFAULT NULL,\n\
  `context` text\n\
) ENGINE=InnoDB DEFAULT CHARSET=utf8;%s\n' % (bcolors.WARNING, bcolors.ENDC))
            sys.stdout.write('%sCREATE USER "%s"@"%s" IDENTIFIED BY "%s";%s\n' % (
                bcolors.WARNING, args.username, args.host, args.password, bcolors.ENDC))
            sys.stdout.write('%sGRANT ALL PRIVILEGES ON `%s`.* TO "%s"@"%s";%s\n' % (
                bcolors.WARNING, args.database, args.username, args.host, bcolors.ENDC))
            sys.stdout.write('%sFLUSH PRIVILEGES;;%s\n' % (bcolors.WARNING, bcolors.ENDC))
            raise StopIteration()

    def watching(self, domain):
        if 'all' in self.domains or (domain is None and 'none' in self.domains):
            return True
        return domain in [s.lower() for s in self.domains]

    """
    Context 1.0.0 format:

        {
            version:  <string> - context version
            id:       <long>   - unique message identifier
            domain:   <string> - domain name of generated event (may be None)
            time:     <int>    - unix timestamp (utc) of event
            level:    <int>    - severity (1=DEBUG, 2=INFO, 4=NOTICE,
                                           8=WARNING, 16=ERROR, 32=CRITICAL,
                                           64=ALERT, 128=EMERGENCY)
            source:   <int>    - source of event (1=statement, 2=error,
                                                  3=exception)
            message:  <string> - the message itself (utf-8)
            filename: <string> - originating filename
            line:     <int>    - originating line number
            context:  <array>  - json encoded context
        }
    """

    def work(self, item):
        try:
            record = json.loads(item['data'])
            if not self.watching(record['domain']):
                return

            self.mysql.query("INSERT into messages ( `domain` ,  `time` ,  `level` ,  `source` , `message` , `filename` , `line` , `context` ) VALUES ('%s', '%s', %d, '%s', '%s', '%s', '%s', '%s')" % (
                self.mysql.escape(record['domain']),
                time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(record['time'])),
                math.log(record['level'], 2) + 1, record['source'],
                self.mysql.escape(record['message']),
                self.mysql.escape(record['filename']),
                record['line'],
                self.mysql.escape(record['context']))
            )

        except (_mysql.ProgrammingError, _mysql.OperationalError) as err:
            if  err.args[0] == 2006:
                self.connect()
                self.work(item)
            else:
                sys.stdout.write('%sMYSQL error: %s%s\n' % (bcolors.FAIL, err, bcolors.ENDC))
            pass
        except TypeError as err:
            sys.stdout.write("%sFormat Error:%s%s\n" % (bcolors.FAIL, err, bcolors.ENDC))
            pass

    def run(self):
        for item in self.pubsub.listen():
            self.work(item)


if __name__ == "__main__":
    domains = args.domains.split(' ')

    sys.stdout.write('%s%s%s%s\n' % (bcolors.UNDERLINE, bcolors.OKGREEN, "S8: Mysql Stasher", bcolors.ENDC))
    sys.stdout.write('%s%s%s\n' % (bcolors.OKGREEN, "Stashing: %s domain(s)" % ', '.join(domains), bcolors.ENDC))
    sys.stdout.write('%s%s%s\n' % (bcolors.OKGREEN, "Press Ctrl-C to exit", bcolors.ENDC))

    r = redis.Redis()
    c = Consumer(r, [args.subscription], [s.lower() for s in domains])
    c.daemon = True
    c.start()

    try:
        while True:
            time.sleep(100)
    except (KeyboardInterrupt, SystemExit, StopIteration):
        pass

"""
TODO
----
Need to be able to filter for event severity and/or event contents
"""
