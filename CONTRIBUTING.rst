Contributing
============

1.  **Please sign one of the contributor license agreements [below][6].**
1.  [File an issue][9] to notify the maintainers about what you're working on.
1.  [Fork the repo][10], develop and [test][11] your code changes, add docs.
1.  Make sure that your commit messages clearly describe the changes.
1.  [Send][12] a pull request.

Here are some guidelines for hacking on `artman`.

Before writing code, file an issue
----------------------------------

Use the issue tracker to start the discussion. It is possible that someone else
is already working on your idea, your approach is not quite right, or that the
functionality exists already. The ticket you file in the issue tracker will be
used to hash that all out.

Fork `artman`
-------------

We will use GitHub's mechanism for [forking][8] repositories and making pull
requests. Fork the repository, and make your changes in the forked repository.

Include tests
-------------

Be sure to add the relevant tests before making the pull request. Docs will be
updated automatically when we merge to `master`, but you should also build
the docs yourself via `tox -e docs` and make sure they're readable.

Make the pull request
---------------------

Once you have made all your changes, tests, and updated the documentation,
make a pull request to move everything back into the main `artman`
repository. Be sure to reference the original issue in the pull request.
Expect some back-and-forth with regards to style and compliance of these
rules.

Using a Development Checkout
----------------------------

You’ll have to create a development environment to hack on
`artman`, using a Git checkout:

-   While logged into your GitHub account, navigate to the `artman`
    [repo][1] on GitHub.
-   Fork and clone the `artman` repository to your GitHub account
    by clicking the "Fork" button.
-   Clone your fork of `artman` from your GitHub account to your
    local computer, substituting your account username and specifying
    the destination as `hack-on-artman`. For example:

    ```bash
    $ cd ${HOME}
    $ git clone git@github.com:USERNAME/artman.git hack-on-artman
    $ cd hack-on-artman
    $ # Configure remotes such that you can pull changes from the artman
    $ # repository into your local repository.
    $ git remote add upstream https://github.com:googleapis/artman
    $ # fetch and merge changes from upstream into master
    $ git fetch upstream
    $ git merge upstream/master
    ```

Now your local repo is set up such that you will push changes to your
GitHub repo, from which you can submit a pull request.

-   Create a virtualenv in which to install `artman`:

    ```bash
    $ cd ~/hack-on-artman
    $ virtualenv -ppython2.7 env
    ```

    Note that very old versions of virtualenv (virtualenv versions
    below, say, 1.10 or thereabouts) require you to pass a
    `--no-site-packages` flag to get a completely isolated environment.

    You can choose which Python version you want to use by passing a
    `-p` flag to `virtualenv`. For example, `virtualenv -ppython2.7`
    chooses the Python 2.7 interpreter to be installed.

    From here on in within these instructions, the
    `~/hack-on-artman/env` virtual environment you created above will be
    referred to as `$VENV`. To use the instructions in the steps that
    follow literally, use the `export VENV=~/hack-on-artman/env`
    command.

-   Install `artman` from the checkout into the virtualenv using
    `setup.py develop`. Running `setup.py develop` **must** be done while
    the current working directory is the `artman` checkout
    directory:

    ```bash
    $ cd ~/hack-on-artman
    $ $VENV/bin/python setup.py develop
    ```

Running Tests
--------------

-   To run all tests for `artman` on a single Python version, run
    `tox` from your development virtualenv (See
    **Using a Development Checkout** above).

-   To run the full set of `artman` tests on all platforms, install
    [`tox`][2] into a system Python.  The `tox` console script will be
    installed into the scripts location for that Python.  While in the
    `artman` checkout root directory (it contains `tox.ini`),
    invoke the `tox` console script.  This will read the `tox.ini` file and
    execute the tests on multiple Python versions and platforms; while it runs,
    it creates a virtualenv for each version/platform combination.  For
    example:

    ```bash
    $ sudo pip install tox
    $ cd ~/hack-on-artman
    $ tox
    ```

-   In order to run the `pypy` environment (in `tox`) you'll need at
    least version 2.6 of `pypy` installed. See the [docs][13] for
    more information.


Contributor License Agreements
------------------------------

Before we can accept your pull requests you'll need to sign a Contributor
License Agreement (CLA):

-   **If you are an individual writing original source code** and **you own
    the intellectual property**, then you'll need to sign an
    [individual CLA][4].
-   **If you work for a company that wants to allow you to contribute your
    work**, then you'll need to sign a [corporate CLA][5].

You can sign these electronically (just scroll to the bottom). After that,
we'll be able to accept your pull requests.

[1]: https://github.com/google/oauth2client
[2]: https://tox.readthedocs.org/en/latest/
[4]: https://developers.google.com/open-source/cla/individual
[5]: https://developers.google.com/open-source/cla/corporate
[6]: #contributor-license-agreements
[8]: https://help.github.com/articles/fork-a-repo/
[9]: #before-writing-code-file-an-issue
[10]: #fork-artman
[11]: #include-tests
[12]: #make-the-pull-request
