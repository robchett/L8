#!/usr/bin/env python
"""
T8.py
Static (mysql) Terminal viewer for the L8 redis-backed logger.

Copyright (C) 2014-2015 Alan McFarlane <alan@node86.com>
Copyright (C) 2014-2015 Rob Chett <robchett@gmail.com>
Copyright (C) 2015 Ben Gosney <bengosney@googlemail.com>
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

import math
import json
import curses
from curses import wrapper
import sys
import _mysql
import _mysql_exceptions
import base64
import argparse
import time
import os.path
import ConfigParser

from data.data import Data

config = ConfigParser.ConfigParser({
    'database': 'S8',
    'password': 'S8',
    'username': 'S8',
    'host': 'localhost',
    'port': '3306',
})

conf_path = os.path.expanduser('~') + '/.t8'

if os.path.isfile(conf_path):
    config.read(conf_path)
else:
    config.add_section('config')

parser = argparse.ArgumentParser(description='Terminal viewer for L8 redis-backed logger.')
parser.add_argument('-d', '--database', default=config.get('config', 'database'))
parser.add_argument('-p', '--password', default=config.get('config', 'password'))
parser.add_argument('-u', '--username', default=config.get('config', 'username'))
parser.add_argument('--host', default=config.get('config', 'host'))
parser.add_argument('--port', default=config.get('config', 'port'))
parser.add_argument('-s', '--startDate')
parser.add_argument('-e', '--endDate')
parser.add_argument('--domain')
parser.add_argument('--method', default='latest', help='Available methods: \n\
list_domains -> show all domains with error count\n\
domain -> show all errors for a domain with counts')
args = parser.parse_args()

if args.method in ['domain']:
    parser.error('A domain is required')


class T8:
    class screens:
        DOMAINS = 1
        ERRORS = 2
        CONTEXT = 3

    def __init__(self, data_source):
        self.domain_max = 0
        self.error_max = 0
        self.context_max = 0
        self.data = data_source
        self.current_screen = self.screens.DOMAINS

        self.domain_index = 0
        self.error_index = 0
        self.context_index = 0
        self.options_index = 0

        self.error_mode = data.mode.totals

        self.window_height = 0
        self.window_width = 0

        self.current_domain = None
        self.current_error = None

        # Setup screen
        self.screen1 = None
        self.screen2 = None
        self.screen3 = None
        self.stdscr = None

        # Create looping function
        try:
            wrapper(self.init_windows)
        except KeyboardInterrupt:
            curses.endwin()
            pass

    def domain_list(self):
        self.clear()
        domains = self.data.domains()
        self.domain_max = len(domains)
        self.screen1.addstr('{0: <{width}}'.format('Domains ({0} of {1}) {2} {3}'.format(self.domain_index + 1, self.domain_max, self.data.get_level_sql(), self.data.get_time_sql()), width=curses.COLS),
                            curses.color_pair(1 if self.screens.DOMAINS != self.current_screen else 3))
        cnt = 0
        self.current_domain = None
        if self.domain_max:
            for i in domains:
                if self.domain_index == cnt:
                    self.current_domain = i
                if self.should_skip(self.domain_index, cnt, self.window_height):
                    self.screen1.addstr('{0: <{width1}}{1: >{width2}}'.format(i.host, i.error_count, width1=curses.COLS - 10, width2=10), curses.color_pair(2 if self.domain_index == cnt else 0))
                cnt += 1
            self.error_list()
        self.refresh()

    def should_skip(self, index, cnt, height):
        skip_cnt = (index - height + 4) if index + 4 > height else 0
        return cnt >= skip_cnt and (cnt - skip_cnt) < height - 2

    def error_list(self):
        self.screen2.addstr('{0: <{width}}'.format('Errors ({0} of {1})'.format(self.error_index + 1, self.error_max), width=curses.COLS), curses.color_pair(1 if self.screens.ERRORS != self.current_screen else 3))
        if self.current_domain:
            errors = self.data.errors(self.current_domain.host, self.error_mode)
            self.error_max = len(errors)
            cnt = 0
            self.current_error = None
            for i in errors:
                if self.error_index == cnt:
                    self.current_error = i
                if self.should_skip(self.error_index, cnt, self.window_height):
                    self.screen2.addstr('{0: <{width1}}:{1: <{width2}}{2: <{width3}}{3: <{width4}}{4: <{width5}}{5: <{width6}}\n'.format(
                        i.file[-30:],
                        i.line,
                        i.message.replace("\n", "|")[-79:],
                        i.level,
                        i.count,
                        Data.format_datetime(i.time),
                        width1=30, width2=5, width3=80, width4=10, width5=5, width6=10
                    ), curses.color_pair(2 if self.error_index == cnt else 0))
                cnt += 1

            self.error_context()
        else:
            self.screen2.addstr('{0: <{width}}'.format('No domain', width=curses.COLS), curses.color_pair(3))

    def error_context(self):
        if self.current_error:
            text = json.dumps(json.loads(base64.b64decode(self.current_error.context)), indent=4).split('\n')
            self.context_max = len(text)
            self.screen3.addstr('{0: <{width}}'.format(
                'Error Context ({0} of {1})'.format(
                    self.context_index,
                    self.context_max
                ),
                width=curses.COLS
            ), curses.color_pair(1 if self.screens.CONTEXT != self.current_screen else 3))
            cnt = 0
            for i in self.current_error.message.split('\n'):
                self.screen3.addstr('{0: <{width}}'.format('{0}'.format(i), width=curses.COLS), curses.color_pair(4))
                cnt += max(math.ceil(len(self.current_error.message) / self.window_width), 1)
            total = self.window_height - cnt
            for i in text:
                if self.should_skip(self.context_index + total - 4, cnt, total):
                    self.screen3.addstr('{0}\n'.format(i))
                cnt += max(math.ceil(len(i) / self.window_width), 1)
        else:
            self.screen3.addstr('{0: <{width}}'.format('No error', width=curses.COLS), curses.color_pair(3))

    def get_help_screen(self):
        self.clear()
        self.screen1.addstr('\
Key commands\n\
    tab : move between windows \n\
    up  : Move through the current window\n\
    down: Move through the current window\n\
    h   : View this screen\n\
    q   : Quit or close a sub screen\n\
    o   : Open the options screen'
                            )

        self.refresh()

        while True:
            c = self.stdscr.getch()
            if c == ord('q'):
                self.options_index = 0
                return

    def get_options_screen(self):
        while True:
            self.clear()
            cnt = 0
            self.screen1.addstr('Options\n')
            self.screen1.addstr('Dates\n')
            self.screen1.addstr('\tStart date: {0}\n'.format(self.data.format_timestamp(self.data.start_time)), curses.color_pair(2 if self.options_index == cnt else 0))
            cnt += 1
            self.screen1.addstr('\tEnd date  : {0}\n'.format(self.data.format_timestamp(self.data.end_time)), curses.color_pair(2 if self.options_index == cnt else 0))
            cnt += 1
            self.screen1.addstr('\n')
            self.screen1.addstr('Error levels\n')

            for i in self.data.levels.keys:
                self.screen1.addstr('\t[{0}] {1}\n'.format('x' if self.data.error_levels[cnt - 2] else ' ', i), curses.color_pair(2 if self.options_index == cnt else 0))
                cnt += 1

            self.refresh()
            c = self.stdscr.getch()
            if c == ord('q'):
                return
            elif c == curses.KEY_UP:
                self.options_index = max(self.options_index - 1, 0)
            elif c == curses.KEY_DOWN:
                self.options_index = min(self.options_index + 1, cnt - 1)
            elif c == ord(' '):
                if self.options_index >= 2:
                    self.data.error_levels[self.options_index - 2] = self.data.error_levels[self.options_index - 2] = not self.data.error_levels[self.options_index - 2]
            elif c == curses.KEY_LEFT:
                if self.options_index == 0:
                    self.data.start_time -= 24 * 60 * 60
                elif self.options_index == 1:
                    self.data.end_time -= 24 * 60 * 60
            elif c == curses.KEY_RIGHT:
                if self.options_index == 0:
                    self.data.start_time += 24 * 60 * 60
                elif self.options_index == 1:
                    self.data.end_time += 24 * 60 * 60

    def refresh(self):
        self.screen1.noutrefresh()
        self.screen2.noutrefresh()
        self.screen3.noutrefresh()
        curses.doupdate()

    def clear(self):
        self.screen1.clear()
        self.screen2.clear()
        self.screen3.clear()

    def init_windows(self, stdscr):
        # Disable echo of key presses
        curses.noecho()
        # Disable key buffer with release on enter
        curses.cbreak()
        # Format cursor keys as constants
        stdscr.keypad(True)
        # Setup colours
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_GREEN)
        curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_RED)
        curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_MAGENTA)

        stdscr.clear()

        self.window_height = (curses.LINES / 3)
        self.window_width = curses.COLS

        # Create a sub window at half height
        self.stdscr = stdscr
        self.screen1 = curses.newwin(self.window_height, self.window_width, 0, 0)
        self.screen2 = curses.newwin(self.window_height, self.window_width, self.window_height, 0)
        self.screen3 = curses.newwin(self.window_height, self.window_width, self.window_height * 2, 0)

        stdscr.refresh()
        self.domain_list()

        while True:
            c = self.stdscr.getch()
            if c == curses.KEY_UP:
                if self.current_screen == self.screens.DOMAINS:
                    self.domain_index = max(self.domain_index - 1, 0)
                    self.error_index = 0
                    self.context_index = 0
                elif self.current_screen == self.screens.ERRORS:
                    self.error_index = max(self.error_index - 1, 0)
                    self.context_index = 0
                elif self.current_screen == self.screens.CONTEXT:
                    self.context_index = max(self.context_index - 1, 0)
                self.domain_list()
            elif c == curses.KEY_DOWN:
                if self.current_screen == self.screens.DOMAINS:
                    self.domain_index = min(self.domain_index + 1, self.domain_max - 1)
                    self.error_index = 0
                    self.context_index = 0
                elif self.current_screen == self.screens.ERRORS:
                    self.error_index = min(self.error_index + 1, self.error_max - 1)
                    self.context_index = 0
                elif self.current_screen == self.screens.CONTEXT:
                    self.context_index = min(self.context_index + 1, self.context_max - 1)
                self.domain_list()
            elif c == ord('a'):
                self.error_mode = data.mode.totals if self.error_mode == data.mode.latest else data.mode.latest
                self.domain_list()
            elif c == ord('\t'):
                self.current_screen = (self.current_screen + 1) if self.current_screen != self.screens.CONTEXT else self.screens.DOMAINS
                self.domain_list()
            elif c == ord('h'):
                self.get_help_screen()
                self.domain_list()
            elif c == ord('o'):
                self.get_options_screen()
                self.domain_list()
            elif c == ord('q'):
                return True


if __name__ == "__main__":
    data = Data(args)
    t8 = T8(data)
