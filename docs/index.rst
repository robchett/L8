L8
==

L8 is an ultra-lightweight PHP based logging system which publishes data directly to a Redis channel.

It can be used as a simple logger supporting 8 different levels complete with custom context, an error handler or an exception handler.
With no dependencies other than PHP and Redis L8 is designed to be easy to use, and provides a high-speed mechanism for pushing logs out of a PHP application with minimal overhead.

Getting it
==========

You can get L8 by grabbing the git repository:

 $ git clone git://github.com/nodealan/l8.git

Compatability with PHP
======================

L8 was written using PHP 5.4.29, however it may be usable on earlier versions with little or no modification. The Redis API is self-contained 

Contents
========

.. toctree::
   :maxdepth: 2

   getting_started
   api_reference
   examples

Indices and tables
==================

* :ref:`search`
