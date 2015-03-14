<?php
/**
 *  Copyright (c) 2014-2015, Alan McFarlane
 *  All Rights Reserved.
 *
 *  Redistribution and use in source and binary forms, with or without
 *  modification, are permitted provided that the following conditions are met:
 *
 *  1.  Redistributions of source code must retain the above copyright notice,
 *      this list of conditions and the following disclaimer.
 *
 *  2.  Redistributions in binary form must reproduce the above copyright
 *      notice, this list of conditions and the following disclaimer in the
 *      documentation and/or other materials provided with the distribution.
 *
 *  3.  Neither the name of the copyright holder nor the names of its
 *      contributors may be used to endorse or promote products derived from
 *      this software without specific prior written permission.
 *
 *  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 *  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 *  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 *  ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
 *  LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 *  CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 *  SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 *  INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 *  CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 *  ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 *  POSSIBILITY OF SUCH DAMAGE.
 */
class M8
{
    // redis configuration
    public static $server  = 'localhost:6379';
    public static $db      = 1;
    public static $channel = 'L8';

    // syslog facilities
    const DEBUG     =   1;
    const INFO      =   2;
    const NOTICE    =   4;
    const WARNING   =   8;
    const ERROR     =  16;
    const CRITICAL  =  32;
    const ALERT     =  64;
    const EMERGENCY = 128;

    // internals
    private static $socket;

    public static function monitor($domain=null)
    {
        // connect to redis server
        if (!isset(static::$socket)) {
            static::$socket = stream_socket_client(static::$server);
            if (static::$socket) {
                static::select(static::$db);
            }
        }

        // make sure the socket was opened
        if (!static::$socket) {
            echo "Cannot connect to redis server\n";

            return false;
        }

        // startup
        echo "L8 command-line monitor\n";
        echo "Press Ctrl-C to exit\n\n";

        // subscribe
        static::subscribe(static::$channel);

        // levels
        $level = [
            static::DEBUG     => 'DEBUG',
            static::INFO      => 'INFO',
            static::NOTICE    => 'NOTICE',
            static::WARNING   => 'WARNING',
            static::ERROR     => 'ERROR',
            static::CRITICAL  => 'CRITICAL',
            static::ALERT     => 'ALERT',
            static::EMERGENCY => 'EMERGENCY',
        ];

        // main loop
        while (1) {
            $data = static::parse();

            if (!is_array($data) || (count($data) != 3)) {
                continue;
            }

            $record = json_decode($data[2]);

            if (is_null($domain) || !strcasecmp($domain, $record->domain)) {
                $record->context = base64_decode($record->context);

                echo strftime('[%Y-%m-%d %H:%M:%S] ', $record->time);

                if (is_null($domain)) {
                    echo "<" . $record->domain . '> ';
                }

                echo implode(' ', [
                        $record->filename . ':' . $record->line,
                        $level[$record->level],
                        '"' . $record->message . '"',
                        static::pretty(json_decode($record->context))
                    ])."\n";
            }
        }
    }

    /* -- */

    private static function subscribe($channel)
    {
        return static::execute(['SUBSCRIBE', $channel]);
    }

    private static function select($index)
    {
        return static::execute(['SELECT', $index]);
    }

    /* -- */

    private static function execute($args)
    {
        $cmd = '*' . count($args) . "\r\n";
        foreach ($args as $arg) {
            $cmd .= '$' . strlen($arg) . "\r\n" . $arg . "\r\n";
        }

        fwrite(static::$socket, $cmd);

        return static::parse();
    }

    private static function parse()
    {
        $line = fgets(static::$socket);

        list($type, $result) = [$line[0], substr($line, 1, strlen($line) - 3)];

        if ($type == '-') {
            throw new Exception($result);
        } elseif ($type == '$') {
            if ($result == -1) {
                $result = null;
            } else {
                $line = fread(static::$socket, $result + 2);
                $result = substr($line, 0, strlen($line) - 2);
            }
        } elseif ($type == '*') {
            $count = (int) $result;

            for ($i = 0, $result = []; $i < $count; $i++) {
                $result[] = static::parse();
            }
        }

        return $result;
    }

    private static function pretty($data)
    {
        if ($data === true) {
            return 'True';
        }
        else if ($data === false) {
            return 'False';
        }
        else if (is_null($data)) {
            return 'null';
        }
        else if (is_numeric($data)) {
            return $data;
        }
        else if (is_string($data)) {
            return '"' . str_replace('"', '\"', $data) . '"';
        }
        else if (is_array($data)) {
            $result = '[ ';
            foreach ($data as $key => $value) {
                $result .= static::pretty($value) . ', ';
            }
            return trim($result, ', ') . ' ]';
        }
        else if (is_object($data)) {
            $result = '{ ';
            foreach ($data as $key => $value) {
                $result .= $key . ':' . static::pretty($value) . ', ';
            }
            return trim($result, ', ') . ' }';
        }
        else {
            return '?';
        }
    }
}

/* -- */

M8::monitor($_SERVER['argc'] == 2 ? $_SERVER['argv'][1] : null);
