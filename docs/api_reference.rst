API Reference
=============

Global Variables
----------------

+----------+---------+------------------+
| Name     | Type    | Default          |
+==========+=========+==================+
| $server  | string  | 'localhost:6379' |
+----------+---------+------------------+
| $db      | integer | 1                |
+----------+---------+------------------+
| $channel | string  | 'L8'             |
+----------+---------+------------------+

Before making any calls to L8, you can alter these settings in order to change the target redis server, database and channel. Please note that doing so may well result in any client monitoring tools to stop operating correctly unless they are updated accordingly.

Example
^^^^^^^

.. code-block:: php

   <?php
   // Setup the L8 environment
    L8::$server = 'db1.example.com:6333';
    L8::db = 0;
    L8::channel = 'L8test';

    // And log an example message
    L8::debug('Example Message');

This will send the log message to the server `db1.example.com` on port `6333`. The message will be published on channel `L8test` with message ID numbers from `L8test_seq` and stored in database `0`.

Severty Constants
-----------------

These constants reflect the actually logging call made and are defined with values to make it simple for listening clients to mask out or ignore certain values with ease.

+-----------+-------+
| Name      | Value |
+===========+=======+
| DEBUG     | 1     |
+-----------+-------+
| INFO      | 2     |
+-----------+-------+
| NOTICE    | 4     |
+-----------+-------+
| WARNING   | 8     |
+-----------+-------+
| ERROR     | 16    |
+-----------+-------+
| CRITICAL  | 32    |
+-----------+-------+
| ALERT     | 64    |
+-----------+-------+
| EMERGENCY | 128   |
+-----------+-------+

Source Constants
----------------

L8 provides the ability to act as an error handler and an exception handler as well as its normal logging facilities. With that in mind, these constants inform clients as to the actual source of the logging event and have values to permit masking by clients as above.

+-------------------+-------+
| Name              | Value |
+===================+=======+
| LOG_STATEMENT     | 1     |
+-------------------+-------+
| ERROR_HANDLER     | 2     |
+-------------------+-------+
| EXCEPTION_HANDLER | 4     |
+-------------------+-------+

Logging Methods
---------------

+-----------+---------------------------------------------+
| Name      | Syntax                                      |
+===========+=============================================+
| debug     | void debug($message, array $context=[])     |
+-----------+---------------------------------------------+
| info      | void info($message, array $context=[])      |
+-----------+---------------------------------------------+
| notice    | void notice($message, array $context=[])    |
+-----------+---------------------------------------------+
| warning   | void warning($message, array $context=[])   |
+-----------+---------------------------------------------+
| error     | void error($message, array $context=[])     |
+-----------+---------------------------------------------+
| critical  | void critical($message, array $context=[])  |
+-----------+---------------------------------------------+
| alert     | void alert($message, array $context=[])     |
+-----------+---------------------------------------------+
| emergency | void emergency($message, array $context=[]) |
+-----------+---------------------------------------------+

Example
^^^^^^^

.. code-block:: php

   <?php

   // Generate a simple notice
   L8::notice('Simple notice');

Error Handling
--------------

L8 can be setup as an error handler as follows:

.. code-block:: php

   <?php

   // Setup L8 as an error handler
   set_error_handler(['L8', 'error_handler']);

   // And trigger a simple error
   $a = 1 / 0;

Exception Handling
------------------

L8 can also be used to handle exceptions as follows:

.. code-block:: php

   <?php

   // Setup L8 as an exception handler
   set_exception_handler(['L8', 'exception_handler']);

   // And trigger a simple exception
   throw new LogicException('Unexpected logic condition');
