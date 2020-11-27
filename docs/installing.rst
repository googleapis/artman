Installation
============

Prerequisites
-------------

Docker
~~~~~~
Because of the many, many things that must be on your system for artman to
do its job, artman utilizes `Docker`_ and ships a container which has
appropriate dependencies available. You will, therefore, need Docker to be
on your system.

.. note::

    It is also possible to run artman locally (use ``--local``) when invoking
    it. This is generally only recommended for development of artman itself,
    but is an option. If you do this, use our `Dockerfile`_ as a reference
    to what dependencies you are likely to need.

.. _`Docker`: https://docker.com/
.. _`Dockerfile`: https://github.com/googleapis/artman/blob/master/Dockerfile

googleapis
~~~~~~~~~~
Currently, artman is primarily used for building Google Cloud client libraries,
and depends on a large, interdependent configuration structure. This is housed
in the `googleapis`_ repository.

In order to run artman, you will need to clone this repository, and generally
you should be in this directory when invoking artman.

.. code-block:: bash

    $ git clone git@github.com:googleapis/googleapis.git googleapis/


Installation
------------

1. If you have not already, install `pip`_ and `virtualenv`_.
   (Use ``which pip`` or ``which virtualenv`` to see if you already have them.)

1. Install Armin Ronacher's `pipsi`_. This is a tool for installing scripts
   on your machine without touching system Python and without having to worry
   about the script's virtual environment. In other words, it is the correct
   tool for exactly this problem.

   .. code-block:: bash

       # This instruction is from the pipsi README; if you have trouble,
       # double-check there.
       $ curl https://raw.githubusercontent.com/mitsuhiko/pipsi/master/get-pipsi.py | python

1. Install artman itself:

   .. code-block:: bash

       $ pipsi install googleapis-artman

   This will place an executable spelled ``artman`` on your path.
   If you need to upgrade artman in the future, you can use
   ``pipsi upgrade googleapis-artman`` to do so.

.. _`pip`: https://pip.pypa.io/en/stable/installing/
.. _`pipsi`: https://github.com/mitsuhiko/pipsi
.. _`virtualenv`: https://virtualenv.pypa.io/en/stable/


Configuration
-------------

The artman tool requires some configuration in order to run (some of this
is legacy from before artman was primarily run in Docker).

When you try to run ``artman`` the first time, it will complain and ask
for a configuration file. Run ``configure-artman`` which will interactively
walk you through the steps to create one, and then place it in the right spot.

The configuration tool will ask you for a "repository root". You should
specify the directory *above* wherever you cloned googleapis to, and then
you can use the defaults for everything else it asks.

This tool will be improved or removed in a future version.
