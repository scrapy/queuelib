========
queuelib
========

Queuelib is a collection of persistent (disk-based) queues for Python.

Queuelib goals are speed and simplicity. It was originally part of the `Scrapy
framework`_ and stripped out on its own library.

Requirements
============

* Python 2.7 or Python 3.3
* no external library requirements

Installation

Installation
============

You can install Queuelib either via the Python Package Index (PyPI) or from
source.

To install using pip::

    $ pip install queuelib

To install using easy_install::

    $ easy_install queuelib

If you have downloaded a source tarball you can install it by running the
following (as root)::

    # python setup.py install

FIFO/LIFO disk queues
=====================

Queuelib provides FIFO and LIFO queue implementations.

Here is an example usage of the FIFO queue::

    >>> from queuelib import FifoDiskQueue
    >>> q = FifoDiskQueue("queuefile")
    >>> q.push('a')
    >>> q.push('b')
    >>> q.push('c')
    >>> q.pop()
    'c'
    >>> q.close()
    >>> q = FifoDiskQueue("queuefile")
    >>> q.pop()
    'b'
    >>> q.pop()
    'a'
    >>> q.pop()
    >>>

The LIFO queue is identical (API-wise), but importing ``LifoDiskQueue``
instead.

PriorityQueue
=============

A discrete-priority queue implemented by combining multiple FIFO/LIFO queues
(one per priority).

First, select the type of QUEUE (FIFO or LIFO)::

    >>> from queuelib import FifoDiskQueue
    >>> q = FifoDiskQueue("somedir")

Then instantiate the Priority Queue with it::

    >>> from queuelib import PriorityQueue
    >>> pq = PriorityQueue(q)

And use it::

    >>> pq.push('a', 3)
    >>> pq.push('b', 1)
    >>> pq.push('c', 2)
    >>> pq.push('d', 2)
    >>> pq.pop()
    'b'
    >>> pq.pop()
    'c'
    >>> pq.pop()
    'd'
    >>> pq.pop()
    'a'

Mailing list
============

Use the `scrapy-users`_ mailing list for questions about Queuelib.

Bug tracker
===========

If you have any suggestions, bug reports or annoyances please report them to
our issue tracker at: http://github.com/scrapy/queuelib/issues/

Contributing
============

Development of Queuelib happens at GitHub: http://github.com/scrapy/queuelib

You are highly encouraged to participate in the development. If you don't like
GitHub (for some reason) you're welcome to send regular patches.

All changes require tests to be merged.

Tests
=====

Tests are located in `queuelib/tests` directory. They can be run using
`nosetests`_ with the following command::

    nosetests

The output should be something like the following::

    $ nosetests
    .............................................................................
    ----------------------------------------------------------------------
    Ran 77 tests in 0.145s

    OK

License
=======

This software is licensed under the BSD License. See the LICENSE file in the
top distribution directory for the full license text.

Versioning
==========

This software follows `Semantic Versioning`_

.. _Scrapy framework: http://scrapy.org
.. _scrapy-users: http://groups.google.com/group/scrapy-users
.. _Semantic Versioning: http://semver.org/
.. _nosetests: https://nose.readthedocs.org/en/latest/
