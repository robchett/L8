#!/usr/bin/env python
"""
A8.py
Context based alert tool based of errors logged by S8

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

import ConfigParser
from data.data import Data
from data.subscriber import Subscriber
from data.bcolors import bcolors
from slacker import Slacker, Error
import redis
import json
import time

class Processor:
    def __init__(self, data):
        self.data = data
        self.config = Config()
        self.domains = {}
        self.redis = redis.Redis()

    def work(self, data):
        host = data['domain']
        if not host in self.domains:
            self.domains[host] = Domain(host, self.config.get_host(host), self.redis)
        self.domains[host].add_error(data)


class Domain:
    def __init__(self, host, config, redis):
        self.host = host
        self.redis = redis  # type: redis.Redis
        self.config = config
        self.error_level = 0
        self.slack = Slacker(self.config['slack_api_key'])

        self.distribution = {}
        self.posts = {}
        self.skipped_posts = 0

        try:
            res = self.get_value('posts', '{}')
            self.posts = json.loads(res.replace("'", '"'))
        except ValueError:
            bcolors.print_colour("Invalid cache read: posts", bcolors.WARNING, bcolors.UNDERLINE)
            print res
            self.reset_posts()
        try:
            res = self.get_value('distribution', '{}')
            self.distribution = json.loads(res.replace("'", '"'))
        except ValueError:
            bcolors.print_colour("Invalid cache read: distribution", bcolors.WARNING, bcolors.UNDERLINE)
            print res
            self.reset_distribution()
        self.skipped_posts = int(self.get_value('skipped_posts', 0))
        self.error_level = int(self.get_value('error_level', 0))

        pass

    def get_value(self, key, default):
        value = self.redis.get('.a8.%s.%s' % (self.host, key))
        if value is None:
            return default
        return value

    def set_value(self, key, value):
        self.redis.set('.a8.%s.%s' % (self.host, key), value)
        pass

    def add_error(self, data):
        level = self.reverse_level(data['level'])
        self.incr_distribution(level)

        self.incr_error_level(int(self.config['weighting_{}'.format(level)]))
        if self.error_level > int(self.config['tolerance']):
            self.alert()
            self.reset_error_level()
        else:
            print "%s: remaining tolerance - %d" % (self.host, int(self.config['tolerance']) - self.error_level)

    def skip(self):
        self.skipped_posts += 1
        self.set_value('skipped_posts', self.skipped_posts)

    def reset_skip(self):
        self.skipped_posts = 0
        self.set_value('skipped_posts', self.skipped_posts)

    def incr_distribution(self, level):
        self.distribution[level] = self.distribution.get(level, 0) + 1
        self.set_value('distribution', json.dumps(self.distribution))
        pass

    def reset_distribution(self):
        self.distribution = {}
        self.set_value('distribution', self.distribution)

    def add_post(self):
        self.posts.append({'time': time.time()})
        self.set_value('posts', json.dumps(self.posts))

    def reset_posts(self):
        self.posts = {}
        self.set_value('posts', self.posts)

    def incr_error_level(self, value):
        self.error_level += value
        self.set_value('error_level', self.error_level)

    def reset_error_level(self):
        self.error_level = 0
        self.set_value('error_level', self.error_level)

    def alert(self):
        posts_within_1min = 0
        posts_within_5min = 0
        posts_within_15min = 0
        posts_within_hour = 0
        for post in self.posts:
            if time.time() - post.get('time') < 60:
                posts_within_1min += 1
            if time.time() - post.get('time') < 60 * 5:
                posts_within_15min += 1
            if time.time() - post.get('time') < 60 * 15:
                posts_within_5min += 1
            if time.time() - post.get('time') < 60 * 60:
                posts_within_hour += 1

        self.posts = [x for x in self.posts if x.get('time') >= 60 * 60]

        if posts_within_1min > 1 or posts_within_5min > 2 or posts_within_15min > 5 or posts_within_hour > 10:
            self.skip()
            return False

        self.add_post()

        channels = self.config['channels']
        if isinstance(channels, basestring):
            channels = json.loads(channels.replace("'", '"'))

        for channel in channels:
            if channel[:6] == 'slack:':
                self.alert_slack_notification(channel[6:], self.skipped_posts, self.distribution)
            else:
                # Other channels we might want to use in the future.
                pass

        self.reset_skip()
        self.reset_distribution()

    def alert_slack_notification(self, channel, skipped, distribution):
        bcolors.print_colour("Posting message to %s\n" % channel, bcolors.WARNING, bcolors.BOLD)
        try:
            message = "%s: tolerance of %d exceeded" % (self.host, int(self.config['tolerance']))
            if skipped:
                message = "%s, %d skipped" % (message, skipped)
            distribution_list = []
            for key, value in distribution.iteritems():
                distribution_list.append({'title': key, 'value': value, "short": True})
            attachments = json.dumps([{'fields': distribution_list}])
            res = self.slack.chat.post_message('%s' % channel, message, username="ErrorBot", icon_url="http://lorempixel.com/48/48/", attachments=attachments)
        except Error as error:
            bcolors.print_colour("Error: %s -> %s\n" % (error.message, channel), bcolors.FAIL)

    def alert_email(self, message, channel):
        pass

    def reverse_level(self, level):
        return {
            '1': 'debug',
            '2': 'info',
            '4': 'notice',
            '8': 'warning',
            '16': 'error',
            '32': 'critical',
            '64': 'alert',
            '128': 'emergency',
        }["%d" % level]


class Config(ConfigParser.ConfigParser):
    def __init__(self):
        import os.path

        ConfigParser.ConfigParser.__init__(self, {
            'tolerance': 1000,
            'slack_api_key': '<your-api-key-here>',
            'channels': [
                'slack:#error_reporting'
            ],
            'weighting_DEBUG': 0,
            'weighting_INFO': 0,
            'weighting_NOTICE': 5,
            'weighting_WARNING': 15,
            'weighting_ERROR': 50,
            'weighting_CRITICAL': 100,
            'weighting_ALERT': 500,
            'weighting_EMERGENCY': 1000,
        })

        conf_path = os.path.expanduser('~') + '/.a8'

        if os.path.isfile(conf_path):
            self.read(conf_path)
        else:
            self.add_section('base')
            self.write(open(conf_path, 'w'))
            bcolors.print_colour("Writing default config to ~/.a8\n", bcolors.OKBLUE, bcolors.BOLD)

    def check_section(self, section):
        if not self.has_section(section):
            self.add_section(section)

    def get_host(self, section):
        if not self.has_section(section):
            self.add_section(section)
        return dict(self.items(section, True))


if __name__ == "__main__":
    from data.config import args as db_args

    bcolors.print_colour("A8: alerting tool\n", bcolors.OKGREEN, bcolors.UNDERLINE)
    bcolors.print_colour("Press Ctrl-C to exit\n", bcolors.OKGREEN, )

    try:
        data = Data(db_args)
        p = Processor(data)
        s = Subscriber()
        s.work(p.work)
    except (KeyboardInterrupt, SystemExit):
        pass
