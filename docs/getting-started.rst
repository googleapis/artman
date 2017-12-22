Getting Started
===============

It is time to build a client library!

Using ``artman`` requires two concepts: (1) pointing to a artman configuration
file, which tells artman what source material it is working off of, and (2)
telling it what you want it to do.

Here is an example command:

.. code-block:: bash

    # Right now, artman is location-aware; you need to be in the
    # googleapis directory for everything to work correctly.
    $ cd /path/to/googleapis/

    # Build the language.v1 API library, and produce a Python client.
    $ artman --config google/cloud/language/artman_language_v1.yaml \
        generate python_gapic

Unpacking that command:

  * The ``--config`` switch (which is actually required) tells artman what
    inputs to use. In this case, the configuration is for the
    `Natural Language API`_.

    .. note::

        As of this writing, some artman YAML configs have a version at the
        end, and some do not. (We are moving in the direction of
        consistently having them.)

  * ``generate`` is the command / verb. (artman also supports ``publish``,
    which is able to, for example, automatically create a pull request on
    GitHub.)

  * ``python_gapic`` is the objective -- the thing you want to be produced.
    You essentially always want a GAPIC (an old code name for the complete,
    auto-generated API client), but seven languages are supported at this
    time; ``ruby_gapic``, ``java_gapic``, etc. will give you what you expect.

The package will be dropped in a newly created ``artman-genfiles/`` directory
within your current working directory; the output of the command will tell
you precisely where it put the library.

.. _`Natural Language API`: https://cloud.google.com/natural-language/
