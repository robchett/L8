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
import math
import redis
import time
import argparse
from data.bcolors import bcolors
from data.subscriber import Subscriber

parser = argparse.ArgumentParser(description='Static (mysql) log for the L8 redis-backed logger.')
parser.add_argument('-s', '--subscription', default='L8')
parser.add_argument('--domains', default='all', help='Domains to filter out, defaults to "all"')
args = parser.parse_args()


class Processor:
    def __init__(self, domains):
        self.map = ['DEBUG', 'INFO', 'NOTICE', 'WARNING', 'ERROR', 'CRITICAL', 'ALERT', 'EMERGENCY']
        self.domains = domains

    def watching(self, domain):
        if 'all' in self.domains or (domain is None and 'none' in self.domains):
            return True
        return domain in [s.lower() for s in self.domains]

    def work(self, record):
        if self.watching(record['domain']):
            bcolors.print_colour(datetime.datetime.fromtimestamp(record['time']).strftime('[%Y-%m-%d %H:%M:%S]'), bcolors.OKBLUE)

            if record['domain'] is not None:
                bcolors.print_colour(' <' + record['domain'] + '> ', bcolors.OKGREEN)

            bcolors.print_colour(' %s "%s"' % (self.map[int(math.log(record['level'], 2))], record['message']), bcolors.WARNING)

            if len(record['filename']):
                bcolors.print_colour(" in ", bcolors.ENDC)
                bcolors.print_colour(record['filename'], bcolors.FAIL)
                if record['line'] > 0:
                    bcolors.print_colour(":%d" % record['line'], bcolors.FAIL)

            bcolors.print_colour(" %s\n" % record['context'], bcolors.ENDC)


if __name__ == "__main__":
    domains = args.domains.split(' ')
    bcolors.print_colour("L8: command-line monitor\n", bcolors.OKGREEN, bcolors.UNDERLINE)
    bcolors.print_colour("Monitoring: %s domain(s)\n" % ', '.join(domains), bcolors.OKGREEN, )
    bcolors.print_colour("Press Ctrl-C to exit\n", bcolors.OKGREEN, )

    try:
        s = Subscriber(args.subscription)
        c = Processor([d.lower() for d in domains])
        s.work(c.work)
    except redis.ConnectionError as err:
        sys.stdout.write('%s%sConnection error%s\n' % (bcolors.UNDERLINE, bcolors.FAIL, bcolors.ENDC))
        sys.stdout.write('%s%s%s\n' % (bcolors.FAIL, err, bcolors.ENDC))
    except (KeyboardInterrupt, SystemExit):
        pass

"""
TODO
----
Need to be able to filter for event severity and/or event contents
"""
