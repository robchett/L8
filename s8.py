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

import json
import redis
import sys
from data.bcolors import bcolors
from data.config import args
from data.data import Data
from data.data import ConnectionError

class Processor:
    def __init__(self, subscription='L8', args=args):
        self.redis = redis.Redis()
        self.pubsub = self.redis.pubsub(ignore_subscribe_messages=True)
        self.pubsub.subscribe(subscription)
        self.domains = args.domains
        try:
            self.data = Data(args)
        except ConnectionError as err:
            Data.invalid_connection(err, args)
            raise StopIteration()

    def work(self):
        for item in self.pubsub.listen():
            record = json.loads(item['data'])
            if self.watching(record['domain']):
                self.data.add_entry(record)

    def watching(self, domain):
        if 'all' in self.domains or (domain is None and 'none' in self.domains):
            return True
        return domain in [s.lower() for s in self.domains]


if __name__ == "__main__":
    domains = args.domains.split(' ')
    sys.stdout.write('%s%s%s%s\n' % (bcolors.UNDERLINE, bcolors.OKGREEN, "S8: Mysql Stasher", bcolors.ENDC))
    sys.stdout.write('%s%s%s\n' % (bcolors.OKGREEN, "Stashing: %s domain(s)" % ', '.join(domains), bcolors.ENDC))
    sys.stdout.write('%s%s%s\n' % (bcolors.OKGREEN, "Press Ctrl-C to exit", bcolors.ENDC))
    try:
        c = Processor(subscription=args.subscription, args=args)
        c.work()
    except (KeyboardInterrupt, SystemExit, StopIteration):
        pass

"""
TODO
----
Need to be able to filter for event severity and/or event contents
"""
