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

At the moment, this library is under development, so please see
`using a development checkout`_ for installation instructions

.. _`using a development checkout`: https://github.com/googleapis/artman/blob/master/CONTRIBUTING.rst#using-a-development-checkout


Usage
-----

Currently, this tool can only be run in the development environment of the
development team, as some dependencies are yet to be published. See USAGE_ for
details.

.. _USAGE: https://github.com/googleapis/artman/blob/master/USAGE.rst


Python Versions
---------------

artman is currently tested with Python 2.7.


Contributing
------------

Contributions to this library are always welcome and highly encouraged.

See the `CONTRIBUTING`_ documentation for more information on how to get started.

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

For detailed documentation of the modules in artman, please watch `DOCUMENTATION`_.

.. _`DOCUMENTATION`: https://googleapis-artman.readthedocs.org/


License
-------

BSD - See `LICENSE`_ for more information.

.. _`LICENSE`: https://github.com/googleapis/artman/blob/master/LICENSE
