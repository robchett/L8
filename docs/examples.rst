Examples
========

Minimalistic
------------

.. code-block:: php

   <?php

   // Log a message at the debug level without context
   L8::debug('L8 is very easy to use');

This of course assumes you have L8.php autoloaded.

Complete
--------

.. code-block:: php

   <?php

   // Make sure the L8 class is loaded
   include_once('/path/to/L8.php');

   // Setup the Redis defaults
   L8::$server = 'localhost:6379';
   L8::$db = 1;
   L8::$channel = 'L8';

   // Setup L8 as an error handler
   set_error_handler(['L8', 'error_handler']);

   // Setup L8 as an exception handler
   set_exception_handler(['L8', 'exception_handler']);

   // Log a message at the debug level without context
   L8::debug('L8 initialization complete');

   // Log a message at the notice level with the contents of $_SERVER as the context
   L8::debug('Server setup', $_SERVER);
