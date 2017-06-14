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
POSSIBILITY OF OF SUCH DAMAGE.
"""

import math

class Levels:
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
        self.error_levels = {
            self.DEBUG: args.eDEBUG == True or args.eDEBUG == '1',
            self.INFO: args.eINFO == True or args.eINFO == '1',
            self.NOTICE: args.eNOTICE == True or args.eNOTICE == '1',
            self.WARNING: args.eWARNING == True or args.eWARNING == '1',
            self.ERROR: args.eERROR == True or args.eERROR == '1',
            self.CRITICAL: args.eCRITICAL == True or args.eCRITICAL == '1',
            self.ALERT: args.eALERT == True or args.eALERT == 'True',
            self.EMERGENCY: args.eEMERGENCY == True or args.eEMERGENCY == '1',
        }

   def get_level_value(self, elevel):
        return math.log(elevel, 2)

   def get_title(self, level):
        return self.keys[self.get_level_value(level)]

   def is_enabled(self, level):
        return self.error_levels[self.get_level_value(level)]