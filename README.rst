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
1. Optional: set up a virtualenv for your Python work. Choose one of
   the following:

   1. (recommended) `virtualenvwrapper`_ so you don't have to keep
      track of where your virtualenv is on the filesystem:

      .. code::

         sudo pip install virtualenv virtualenvwrapper
         mkvirtualenv --python=`which python3` artman

      To use this virtual environment later:

      .. code ::

         workon artman

   2. `virtualenv`_ in your current directory:

      .. code::

         sudo pip install virtualenv
         virtualenv env
         source env/bin/activate

2. Install artman directly from pip:

   .. code::

      pip install googleapis-artman

You may need root privileges if you are not installing inside of a virtualenv.
This will make the ``artman`` command available on your system.

.. _`virtualenvwrapper`: https://virtualenvwrapper.readthedocs.io/en/latest/
.. _`virtualenv`: https://pypi.python.org/pypi/virtualenv


Prerequisites
-------------
1. Install `googleapis`_
2. Install `toolkit`_
3. Install Java
4. Some languages may have additional dependencies; refer to the ``Dockerfile``
   in this repository for canonical installation requirements.

.. _`googleapis`: https://github.com/googleapis/googleapis
.. _`toolkit`: https://github.com/googleapis/toolkit


Usage
-----

Before you can use artman, you will need a configuration file. You can run
``configure-artman`` to create a simple configuration file.

For building a GAPIC (the most common task), the usage looks like:

.. code::

    artman --api pubsub --language python

Artman also takes a ``--publish`` argument to decide where to stage the
code. Using ``--publish github`` will create a pull request on GitHub
automatically.


Python Versions
---------------

artman is currently tested with Python 2.7, Python 3.4, Python 3.5,
and Python 3.6.

.. note::

    The authors of this README are humans, and this is an exceptionally
    easy spot to end up out of date.

    Our ``nox.py`` and ``.circleci/config.yml`` files are the real source
    of truth for what versions of Python we test against.


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
