#!/usr/bin/env python
"""
M8.php
Command-Line monitor for the L8 redis-backed logger.

Copyright (C) 2014-2015 Alan McFarlane <alan@node86.com>
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
import time
import re
import base64
import argparse
from data.bcolors import bcolors


parser = argparse.ArgumentParser(description='Static (mysql) log for the L8 redis-backed logger.')
parser.add_argument('-s', '--subscription', default='L8')
parser.add_argument('--domains', default='all', help='Domains to filter out, defaults to "all"')
args = parser.parse_args()


class Consumer(threading.Thread):
    def __init__(self, r, channels, domains):
        threading.Thread.__init__(self)
        self.redis = r
        self.pubsub = self.redis.pubsub()
        self.pubsub.subscribe(channels)
        self.map = ['DEBUG', 'INFO', 'NOTICE', 'WARNING', 'ERROR', 'CRITICAL',
                    'ALERT', 'EMERGENCY']
        self.domains = domains

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

            sys.stdout.write(
                bcolors.OKBLUE +
                datetime.datetime.fromtimestamp(record['time']).strftime('[%Y-%m-%d %H:%M:%S]') +
                bcolors.ENDC
            )

            if record['domain'] is not None:
                sys.stdout.write(
                    bcolors.OKGREEN +
                    ' <' + record['domain'] + '> ' +
                    bcolors.ENDC
                )

            sys.stdout.write(bcolors.WARNING)
            sys.stdout.write(' %s "%s"' % (self.map[int(math.log(record['level'], 2))], record['message']))
            sys.stdout.write(bcolors.ENDC)

            if len(record['filename']):
                sys.stdout.write(" in %s%s" % (bcolors.FAIL, record['filename']))
                if record['line'] > 0:
                    sys.stdout.write(":%d" % record['line'])
                sys.stdout.write(bcolors.ENDC);
            sys.stdout.write(' ');

            regex = re.compile('^([A-Za-z0-9+/]{4})*([A-Za-z0-9+/]{4}|[A-Za-z0-9+/]{3}=|[A-Za-z0-9+/]{2}==)$')
            if (regex.match(record['context'])):
                context = base64.b64decode(record['context'])
            else:
                context = record['context']

            sys.stdout.write(json.dumps(context))
            sys.stdout.write("\n")

        except (TypeError, ValueError):
            # ignore any message that cannot be correctly decoded
            pass

    def run(self):
        for item in self.pubsub.listen():
            self.work(item)


if __name__ == "__main__":
    domains = args.domains.split(' ')

    sys.stdout.write('%s%s%s%s\n' % (bcolors.UNDERLINE, bcolors.OKGREEN, "L8: command-line monitor", bcolors.ENDC))
    sys.stdout.write('%s%s%s\n' % (bcolors.OKGREEN, "Monitoring: %s domain(s)" % ', '.join(domains), bcolors.ENDC))
    sys.stdout.write('%s%s%s\n' % (bcolors.OKGREEN, "Press Ctrl-C to exit", bcolors.ENDC))

    try:
        r = redis.Redis()
        r.ping()
        c = Consumer(r, [args.subscription], [s.lower() for s in domains])
        c.daemon = True
        c.start()

        try:
            while True:
                time.sleep(100)
        except (KeyboardInterrupt, SystemExit):
            pass
    except redis.ConnectionError as err:
        sys.stdout.write('%s%sConnection error%s\n' % (bcolors.UNDERLINE, bcolors.FAIL, bcolors.ENDC))
        sys.stdout.write('%s%s%s\n' % (bcolors.FAIL, err, bcolors.ENDC))
        sys.exit()

"""
TODO
----
Need to be able to filter for event severity and/or event contents
"""
