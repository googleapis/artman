Google API Artifact Manager
===========================

Google API Artifact Manager (``artman``) is a program used to automate the
generaton and publishing of API client libraries.

In order to be consumed by artman, APIs require:

  * A `Protocol Buffers`_ description of the API, specified using proto3
    syntax.
  * A `service configuration`_ stub. This is YAML configuration which
    designates how the API is housed within Google's infrastructure.
  * A GAPIC configuration. This provides extra information specific to
    generating a client library.
  * An artman configuration. This is the file artman uses as the entry point,
    and it points to the previous items in this list.

The artman tool is a wrapper around `toolkit`_; it takes the configuration
enumerated above, normalizes it, and sends it to toolkit, which generates
a client library on disk, and then artman performs some concluding cleanup.

Client libraries produced in this way are executable "out of the box", and
include basic reference documentation, and appropriate packaging and
metadata files.

.. _`Protocol Buffers`: https://developers.google.com/protocol-buffers/
.. _`service configuration`: https://cloud.google.com/service-management/overview#service_configurations
.. _`toolkit`: https://github.com/googleapis/toolkit

Installing
==========

If your goal is just to use ``artman`` (rather than contribute to it), a
standard pip install is probably not the right thing; we recommend
the use of `pipsi`_ instead.

View our `installation guide`_ to get going.

.. _`pipsi`: https://github.com/mitsuhiko/pipsi
.. _`installation guide`: https://googleapis-artman.readthedocs.io/en/latest/installing.html

Documentation
=============

Documentation is available on `Read the Docs`_.

.. _`Read the Docs`: https://googleapis-artman.readthedocs.io/
