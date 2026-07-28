========
queuelib
========

.. image:: https://img.shields.io/pypi/v/queuelib.svg
   :target: https://pypi.python.org/pypi/queuelib

.. image:: https://img.shields.io/pypi/pyversions/queuelib.svg
   :target: https://pypi.python.org/pypi/queuelib

.. image:: https://github.com/scrapy/queuelib/actions/workflows/tests-ubuntu.yml/badge.svg
   :target: https://github.com/scrapy/queuelib/actions/workflows/tests-ubuntu.yml

.. image:: https://img.shields.io/codecov/c/github/scrapy/queuelib/master.svg
   :target: http://codecov.io/github/scrapy/queuelib?branch=master
   :alt: Coverage report


Queuelib is a Python library that implements object collections which are stored
in memory or persisted to disk, provide a simple API, and run fast.

Queuelib provides collections for queues_ (FIFO), stacks_ (LIFO), queues
sorted by priority and queues that are emptied in a round-robin_ fashion.

.. note:: Queuelib collections are not thread-safe.

Queuelib supports Python 3.10+ and has no dependencies.

.. _queues: https://en.wikipedia.org/wiki/FIFO_(computing_and_electronics)
.. _round-robin: https://en.wikipedia.org/wiki/Round-robin_scheduling
.. _stacks: https://en.wikipedia.org/wiki/Stack_(abstract_data_type)

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
    >>> q.push(b'a')
    >>> q.push(b'b')
    >>> q.push(b'c')
    >>> q.pop()
    b'a'
    >>> q.close()
    >>> q = FifoDiskQueue("queuefile")
    >>> q.pop()
    b'b'
    >>> q.pop()
    b'c'
    >>> q.pop()
    >>>

The LIFO queue is identical (API-wise), but importing ``LifoDiskQueue``
instead.

PriorityQueue
=============

A discrete-priority queue implemented by combining multiple FIFO/LIFO queues
(one per priority).

First, select the type of queue to be used per priority (FIFO or LIFO)::

    >>> from queuelib import FifoDiskQueue
    >>> qfactory = lambda priority: FifoDiskQueue('queue-dir-%s' % priority)

Then instantiate the Priority Queue with it::

    >>> from queuelib import PriorityQueue
    >>> pq = PriorityQueue(qfactory)

And use it::

    >>> pq.push(b'a', 3)
    >>> pq.push(b'b', 1)
    >>> pq.push(b'c', 2)
    >>> pq.push(b'd', 2)
    >>> pq.pop()
    b'b'
    >>> pq.pop()
    b'c'
    >>> pq.pop()
    b'd'
    >>> pq.pop()
    b'a'

RoundRobinQueue
===============

Has nearly the same interface and implementation as a Priority Queue except
that each element must be pushed with a (mandatory) key.  Popping from the
queue cycles through the keys "round robin".

Instantiate the Round Robin Queue similarly to the Priority Queue::

    >>> from queuelib import RoundRobinQueue
    >>> rr = RoundRobinQueue(qfactory)

And use it::

    >>> rr.push(b'a', '1')
    >>> rr.push(b'b', '1')
    >>> rr.push(b'c', '2')
    >>> rr.push(b'd', '2')
    >>> rr.pop()
    b'a'
    >>> rr.pop()
    b'c'
    >>> rr.pop()
    b'b'
    >>> rr.pop()
    b'd'

Disk persistence
================

``FifoDiskQueue`` and ``LifoDiskQueue`` write their items to the path they get
on instantiation, so that a queue can be resumed later, even by a different
process.

Each class uses that path differently:

-   ``FifoDiskQueue`` uses a directory, which it creates, together with any
    missing parent directory. Items go into chunk files (``q00000``,
    ``q00001``, etc.), each holding up to ``chunksize`` items, and the queue
    also keeps an ``info.json`` file there for its own bookkeeping.

-   ``LifoDiskQueue`` uses a single file, whose parent directory must already
    exist.

The layout and the contents of those files are an implementation detail that
may change in any release. Do not read or write them yourself, and do not
expect a queue written by one version of Queuelib to be readable by a
different one.

Always close disk queues
------------------------

While a disk queue is open, its bookkeeping (number of items, read and write
positions) only lives in memory, and ``close()`` is what writes it to disk.
Queuelib never calls ``fsync()`` either, and ``LifoDiskQueue`` writes items
through a buffered file object, so the most recent items may not have reached
the disk at all.

Calling ``close()`` is hence mandatory::

    from contextlib import closing

    with closing(FifoDiskQueue("queuedir")) as q:
        q.push(b'a')

If a process ends without calling ``close()``, the queue on disk keeps the
bookkeeping that the last ``close()`` call wrote, which no longer matches the
files. Items pushed since then become unreachable, and using the queue again
is unsafe: it may report a wrong length, return items that had already been
popped, delete files that still contain items, or raise ``OSError``. Queuelib
offers no way to repair or to recover such a queue.

Empty queues delete their files
-------------------------------

``close()`` on an empty queue deletes its file, or, in the case of
``FifoDiskQueue``, its chunk files and its ``info.json`` file, and also its
directory if nothing else remains in it. Using that same path again creates a
new, empty queue.

Reopening a FifoDiskQueue keeps its chunk size
----------------------------------------------

``FifoDiskQueue`` stores its ``chunksize`` when creating a queue, and reuses
the stored value when reopening one, ignoring the ``chunksize`` parameter.

Use one queue object per path at a time
---------------------------------------

Queuelib does not lock the files that it uses. On top of not being
thread-safe, a given path must not be used by more than one open queue object
at a time, in the same process or not. Such queue objects overwrite each
other's items and bookkeeping; for example, two ``FifoDiskQueue`` objects on
the same directory return the same items, and their ``close()`` calls may
raise ``FileNotFoundError``.

Persisting a PriorityQueue or a RoundRobinQueue
-----------------------------------------------

``PriorityQueue`` and ``RoundRobinQueue`` do not write anything to disk
themselves; their persistence comes entirely from the queues that ``qfactory``
builds, and it is up to ``qfactory`` to map a priority or a key to a valid
path.

Their ``close()`` method returns the priorities or keys whose underlying queue
was not empty. Storing that value is your responsibility, and so is passing it
back as ``startprios`` or ``start_domains`` on the next run::

    >>> import json
    >>> from queuelib import FifoDiskQueue, PriorityQueue
    >>> qfactory = lambda priority: FifoDiskQueue('queue-dir-%s' % priority)
    >>> pq = PriorityQueue(qfactory)
    >>> pq.push(b'a', 3)
    >>> active = pq.close()
    >>> with open('active.json', 'w') as f:
    ...     json.dump(active, f)
    ...
    >>> with open('active.json') as f:
    ...     startprios = json.load(f)
    ...
    >>> pq = PriorityQueue(qfactory, startprios)
    >>> pq.pop()
    b'a'

Priorities and keys that you do not pass back are not detected, and the items
in their queues stay on disk, unreachable.

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
