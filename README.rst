gapi-pipeline
=============

Installation
------------

Install tox if it has not already been installed:

  ::
     $ sudo pip install tox  # done once, installed globally

Create, then activate the tox development environment:

  ::
     $ tox -e py27
     $ . .tox/develop/bin/activate
     $(develop) ...

Once done developing, deactivate the development environment:

  ::
     $(develop) deactivate
