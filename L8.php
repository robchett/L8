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

class L8
{
    // redis configuration
    public static $server  = 'localhost:6379';
    public static $db      = 1;
    public static $channel = 'L8';      // NB will also use <$channel>_seq

    // syslog facilities
    const DEBUG     =   1;
    const INFO      =   2;
    const NOTICE    =   4;
    const WARNING   =   8;
    const ERROR     =  16;
    const CRITICAL  =  32;
    const ALERT     =  64;
    const EMERGENCY = 128;

    // data source
    const LOG_STATEMENT     = 1;
    const ERROR_HANDLER     = 2;
    const EXCEPTION_HANDLER = 3;

    // internals
    private static $socket;
    private static $domain;

    /* -- */

    public static function debug($message, array $context=[])
    {
        static::log(static::DEBUG, $message, $context);
    }

    public static function info($message, array $context=[])
    {
        static::log(static::INFO, $message, $context);
    }

    public static function notice($message, array $context=[])
    {
        static::log(static::NOTICE, $message, $context);
    }

    public static function warning($message, array $context=[])
    {
        static::log(static::WARNING, $message, $context);
    }

    public static function error($message, array $context=[])
    {
        static::log(static::ERROR, $message, $context);
    }

    public static function critical($message, array $context=[])
    {
        static::log(static::CRITICAL, $message, $context);
    }

    public static function alert($message, array $context=[])
    {
        static::log(static::ALERT, $message, $context);
    }

    public static function emergency($message, array $context=[])
    {
        static::log(static::EMERGENCY, $message, $context);
    }

    /* -- */

    private static function log($level, $message, array $context=[])
    {
        if (count($trace = debug_backtrace(false, 2)) > 1) {
            $file = $trace[1]['file'];
            $line = $trace[1]['line'];
        } else {
            list($file, $line) = ['', 0];
        }

        return static::write($level, static::LOG_STATEMENT, $message, $file,
                             $line, $context);
    }

    /* -- */

    public static function error_handler($errno, $message, $file='', $line=0,
                                         $context=[])
    {
        if (!is_array($context)) {
            $context = [$context];
        }

        $map = [
            E_ERROR             => ['E_ERROR',             static::ERROR],
            E_WARNING           => ['E_WARNING',           static::WARNING],
            E_PARSE             => ['E_PARSE',             static::ERROR],
            E_NOTICE            => ['E_NOTICE',            static::NOTICE],
            E_CORE_ERROR        => ['E_CORE_ERROR',        static::ERROR],
            E_CORE_WARNING      => ['E_CORE_WARNING',      static::WARNING],
            E_COMPILE_ERROR     => ['E_COMPILE_ERROR',     static::ERROR],
            E_COMPILE_WARNING   => ['E_COMPILE_WARNING',   static::WARNING],
            E_USER_ERROR        => ['E_USER_ERROR',        static::ERROR],
            E_USER_WARNING      => ['E_USER_WARNING',      static::WARNING],
            E_USER_NOTICE       => ['E_USER_NOTICE',       static::NOTICE],
            E_STRICT            => ['E_STRICT',            static::WARNING],
            E_RECOVERABLE_ERROR => ['E_RECOVERABLE_ERROR', static::WARNING],
            E_DEPRECATED        => ['E_DEPRECATED',        static::WARNING],
            E_USER_DEPRECATED   => ['E_USER_DEPRECATED',   static::WARNING],
        ];

        list($prefix, $level) = array_key_exists($errno, $map)
                              ? $map[$errno]
                              : ['E_UNKOWN(' . $errno . ')', static::ERROR];

        static::write($level, static::ERROR_HANDLER, $prefix . ':' . $message,
                      $file, $line, $context);
    }

    public static function exception_handler($e)
    {
        static::write(static::ERROR, static::EXCEPTION_HANDLER,
                      $e->getMessage(), $e->getFile(), $e->getLine(), []);
    }

    /* -- */

    private static function write($level, $source, $message, $file, $line,
                                  $context)
    {
        // connect to redis server
        if (!isset(static::$socket)) {
            static::$socket = stream_socket_client(static::$server);
            if (static::$socket) {
                static::select(static::$db);

                static::$domain = array_key_exists('SERVER_NAME', $_SERVER)
                                ? strtolower($_SERVER['SERVER_NAME'])
                                : 'none';
            }
        }

        // make sure the socket was opened
        if (!static::$socket) {
            return false;
        }

        // generate the atomic log entry id #
        $id = static::incr(static::$channel . '_seq');
        if ($id == '9223372036854775807') {                 // 2^63-1
            static::set(static::$channel . '_seq', 0);
        }

        // construct the data record
        $record = json_encode(
            [
                'id'       => $id,
                'domain'   => static::$domain,
                'time'     => time(),
                'level'    => $level,
                'source'   => $source,
                'message'  => $message,
                'filename' => $file,
                'line'     => $line,
                'context'  => base64_encode(json_encode($context)),
            ]
        );

        static::publish(static::$channel, $record);

        return true;
    }

    /* -- */

    private static function incr($key)
    {
        return static::execute(['INCR', $key]);
    }

    private static function publish($channel, $message)
    {
        return static::execute(['PUBLISH', $channel, $message]);
    }

    private static function select($index)
    {
        return static::execute(['SELECT', $index]);
    }

    private static function set($key, $value)
    {
        return static::execute(['SET', $key, $value]);
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
}
