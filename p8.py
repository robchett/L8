#!/usr/bin/env python
"""
P8.py
Proxy for the L8 redis-backed logger.

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

import redis
import argparse
from data.subscriber import Subscriber
from data.bcolors import bcolors

parser = argparse.ArgumentParser(description='Proxy for the L8 redis-backed logger.')
parser.add_argument('host')
parser.add_argument('-p', '--port', default='6379')
parser.add_argument('-s', '--subscription', default='L8')
parser.add_argument('-v', '--verbose', action='store_true')
args = parser.parse_args()


class Processor:
    def __init__(self, channel):
        self.destin = redis.Redis(args.host, args.port, socket_connect_timeout=1)
        self.destin.ping()
        self.channel = channel

    def work(self, item):
        if args.verbose:
            bcolors.print_colour("Log: %s\n" % item['data'], bcolors.OKGREEN)
        self.destin.publish(self.channel, item['data'])


if __name__ == "__main__":
    bcolors.print_colour("P8: L8 proxy\n", bcolors.OKGREEN, bcolors.UNDERLINE)
    bcolors.print_colour('Proxy endpoint: %s:%s\n' % (args.host, args.port), bcolors.OKGREEN)
    bcolors.print_colour("Press Ctrl-C to exit\n", bcolors.OKGREEN)

    try:
        c = Processor(args.subscription)
        s = Subscriber(args.subscription)
        s.work_raw(c.work)
    except redis.ConnectionError as err:
        bcolors.print_colour('Connection error\n', bcolors.FAIL, bcolors.UNDERLINE)
        bcolors.print_colour(str(err), bcolors.FAIL)
    except (KeyboardInterrupt, SystemExit):
        pass
