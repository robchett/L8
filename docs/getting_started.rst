Getting Started
===============

You will need to ensure that L8.php is loaded by your auto-loader, or simply include it prior to using it with:

.. code-block:: php

    <?php

    include_once('/path/to/L8.php');

Basic Logging
-------------

L8 supports 8 levels of logging from DEBUG to EMERGENCY, each call requiring a message and taking an optional context.

Messages are simple strings, they should ideally be short, but informative but need not contain positional information such as file name or line number, nor should they contain variable data. For example:

.. code-block:: php

    <?php

    include_once('/path/to/L8.php');

    L8::debug('Initialized');
    L8::debug('Validating POST data', $_POST);
    L8::debug('Computed MD5 sum', ['md5sum' => $md5sum]);

Which might produce something like: ::

    [2015-03-14 08:42:35] <none> /example1.php:8 DEBUG "Initialized" 
    [2015-03-14 08:42:36] <none> /example1.php:12 DEBUG "Validating POST data" { project_name:"L8", version:1 }
    [2015-03-14 08:42:37] <none> /example1.php:16 DEBUG "Computed MD5 sum" { md5sum:"a1162516811d92197c7aa0f9d9c15998" }

Log Levels
----------

In keeping with syslog severity indicators, L8 has 8 different log levels, and 8 different logging functions: ::

    debug
    info
    notice
    warning
    error
    critical
    alert
    emergency

Using the Context
-----------------

Each logging function takes an optional context parameter which if present, must be an array. The contents of the context are pretty much up to you although to make things simple for applications subscribing to the log, you should use only simply elements: numbers, strings, booleans, arrays (both indexed and associative) and null. Objects will not be able to decoded by any non-PHP based monitoring tool and must not be specified.
