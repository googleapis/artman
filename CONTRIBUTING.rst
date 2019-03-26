Contributing
============

Here are some guidelines for hacking on `artman`_.

-  Please **sign** one of the `Contributor License Agreements`_ below.
-  `File an issue`_ to notify the maintainers about what you're working on.
-  `Fork the repo`_; develop and `test your code changes`_; add docs.
-  Make sure that your `commit messages`_ clearly describe the changes.
-  `Make the pull request`_.

.. _`Fork the repo`: https://help.github.com/articles/fork-a-repo
.. _`forking`: https://help.github.com/articles/fork-a-repo
.. _`commit messages`: http://chris.beams.io/posts/git-commit/

.. _`File an issue`:

Before writing code, file an issue
----------------------------------

Use the issue tracker to start the discussion. It is possible that someone else
is already working on your idea, your approach is not quite right, or that the
functionality exists already. The ticket you file in the issue tracker will be
used to hash that all out.

Fork `artman`
-------------

We will use GitHub's mechanism for `forking`_ repositories and making pull
requests. Fork the repository, and make your changes in the forked repository.

.. _`test your code changes`:

Include tests
-------------

Be sure to add relevant tests and then run them using :code:`nox` before making the pull request.

Docs will be updated automatically when we merge to `master`, but
you should also build the docs yourself via :code:`nox -e docs`, making sure
that the docs build OK and that they are readable.

.. _`nox`: https://nox.readthedocs.io/en/latest/

Make the pull request
---------------------

Once you have made all your changes, tested, and updated the documentation,
make a pull request to move everything back into the main `artman`_
repository. Be sure to reference the original issue in the pull request.
Expect some back-and-forth with regards to style and compliance of these
rules.

Using a Development Checkout
----------------------------

You’ll have to create a development environment to hack on
`artman`_, using a Git checkout:

-   While logged into your GitHub account, navigate to the
    `artman repo`_ on GitHub.
-   Fork and clone the `artman` repository to your GitHub account
    by clicking the "Fork" button.
-   Clone your fork of `artman` from your GitHub account to your
    local computer, substituting your account username and specifying
    the destination as `hack-on-artman`. For example:

  .. code:: bash

    cd ${HOME}
    git clone git@github.com:USERNAME/artman.git hack-on-artman
    cd hack-on-artman

    # Configure remotes such that you can pull changes from the artman
    # repository into your local repository.
    git remote add upstream https://github.com/googleapis/artman.git

    # fetch and merge changes from upstream into master
    git fetch upstream
    git merge upstream/master


Now your local repo is set up such that you will push changes to your
GitHub repo, from which you can submit a pull request.

-   Check that the Protobuf package is installed by running:

  .. code:: bash

    protoc

-   If not installed, install the Protobuf package
    (https://github.com/google/protobuf) and add the installation directory to `PATH`.

-   Create use tox to create development virtualenv in which `artman`_ is installed:

  .. code:: bash

    sudo pip install virtualenv virtualenvwrapper
    # Edit shell startup file to enable virtualenvwrapper, see:
    # http://virtualenvwrapper.readthedocs.io/en/latest/install.html#shell-startup-file
    mkvirtualenv --python=`which python3` artman
    pip install -e .

-   This creates a virtualenv named `artman` that has artman installed.
    Activate it to use artman locally, e.g, from the python prompt.

  .. code:: bash

    cd ~/hack-on-artman
    workon artman

.. _`artman`: https://github.com/googleapis/artman
.. _`artman repo`: https://github.com/googleapis/artman


Running Tests
-------------

-   To run the full set of `artman` tests on all platforms, install
    `nox`_ into a system Python.  The :code:`nox` console script will be
    installed into the scripts location for that Python.  While in the
    `artman` checkout root directory (it contains :code:`nox.py`),
    invoke the `nox` console script.  This will read the :code:`nox.py` file
    and execute the tests on multiple Python versions and platforms; while
    it runs, it creates a virtualenv for each version/platform combination. For
    example:

  .. code:: bash

      sudo pip install nox-automation
      cd ~/hack-on-artman
      nox

-   To run the full set of artman smoke tests, you need to install docker
    installed on your machine, and run the following at the root of your
    artman source directory:

  .. code:: bash

      docker pull googleapis/artman:latest
      docker run -it \
        -v ${PWD}:/usr/src/artman \
        googleapis/artman:latest \
        /bin/bash -c  "pip uninstall -y googleapis-artman; \
        pip install -e /usr/src/artman/; \
        /usr/src/artman/test/smoketest_artman.py --apis=pubsub,vision"

      # Optionally, you can mount your local toolkit for testing:
      docker run -it \
        -v ${PWD}:/usr/src/artman \
        -v {REPLACE_WITH_LOCAL_TOOLKIT_DIR}:/toolkit \
        googleapis/artman:latest \
        /bin/bash -c  "pip uninstall -y googleapis-artman; \
        pip install -e /usr/src/artman/; \
        /usr/src/artman/test/smoketest_artman.py --apis=pubsub,vision"

Contributor License Agreements
------------------------------

Before we can accept your pull requests you'll need to sign a Contributor
License Agreement (CLA):

-   **If you are an individual writing original source code** and **you own
    the intellectual property**, then you'll need to sign an
    `individual CLA`_.
-   **If you work for a company that wants to allow you to contribute your
    work**, then you'll need to sign a `corporate CLA`_.

You can sign these electronically (just scroll to the bottom). After that,
we'll be able to accept your pull requests.

.. _`individual CLA`: https://developers.google.com/open-source/cla/individual
.. _`corporate CLA`: https://developers.google.com/open-source/cla/corporate
