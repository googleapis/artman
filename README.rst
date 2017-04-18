Google API Artifact Manager
===========================

Google API Artifact manager (artman) is a set of modules used to automate the
creation of software artifacts related to APIS defined using `protobuf`_ IDL.

artman is an extensible framework that is responsible for creating all artifacts
related to an API including

- distribution packages in all supported programming languages
- generic documentation websites
- language-specific documentation websites (javadoc, readthedocs, etc)

from the protobuf source IDL and additional configuration in YAML files.

.. _`protobuf`: https://github.com/google/protobuf


Installation
------------

You can now install artman directly from pip:

.. code::

    pip install googleapis-artman

You may need root privileges if you are not installing inside of a virtualenv.
This will make the ``artman`` command available on your system.


Usage
-----

Before you can use artman, you will need a configuration file. You can run
``artman init`` to create a simple configuration file.

For building a GAPIC (the most common task), the usage looks like:

.. code::

    artman --api pubsub --language python

This assumes that you have checkouts of both `googleapis`_ and `toolkit`_
on your system (and that toolkit is able to run; e.g. you need Java).

Some languages may have additional dependencies; refer to the ``Dockerfile``
in this repository for canonical installation requirements.

.. _`googleapis`: https://github.com/googleapis/googleapis
.. _`toolkit`: https://github.com/googleapis/toolkit

Artman also takes a ``--publish`` argument to decide where to stage the
code. Using ``--publish github`` will create a pull request on GitHub
automatically.


Python Versions
---------------

artman is currently tested with Python 2.7 and Python 3.4.


Contributing
------------

Contributions to this library are always welcome and highly encouraged.

See the `CONTRIBUTING`_ documentation for more information on how to get
started.

.. _`CONTRIBUTING`: https://github.com/googleapis/artman/blob/master/CONTRIBUTING.rst


Versioning
----------

This library follows `Semantic Versioning`_

It is currently in major version zero (``0.y.z``), which means that anything
may change at any time and the public API should not be considered
stable.

.. _`Semantic Versioning`: http://semver.org/


Details
-------

For detailed documentation of the modules in artman, please watch
`DOCUMENTATION`_.

.. _`DOCUMENTATION`: https://googleapis-artman.readthedocs.org/


License
-------

BSD - See `LICENSE`_ for more information.

.. _`LICENSE`: https://github.com/googleapis/artman/blob/master/LICENSE
