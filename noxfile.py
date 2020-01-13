# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import

import nox
import os


@nox.session(python=['3.4', '3.5', '3.6', '3.7'])
def unit_tests(session):
    """Run the unit test suite."""

    # Install all test dependencies, then install this package in-place.
    session.install('mock', 'pytest', 'pytest-cov', 'pyfakefs',
                    'restructuredtext_lint')
    session.install('-e', '.')

    # Run py.test against the unit tests.
    session.run('py.test', '-rxs', '--cov', '--cov-append', '--cov-report=')


@nox.session(python='3.6')
def lint(session):
    """Run the linter."""
    session.install('flake8')
    session.run('flake8', '--max-complexity=8', 'artman',
                '--exclude=test/output', 'test')


@nox.session(python='3.6')
def coverage(session):
    """Provide a coverage report."""
    session.install('coverage')
    try:
        # session.run('coverage', 'report')
        session.run('coverage', 'html')
    finally:
        session.run('coverage', 'erase')


@nox.session(python='3.6')
def docs(session):
    """Build the docs."""

    # Install Sphinx and also all of the google-cloud-* packages.
    session.chdir(os.path.realpath(os.path.dirname(__file__)))
    session.install('setuptools >= 36.4.0', 'sphinx >= 1.6.3', '.')

    # Build the docs!
    session.run('rm', '-rf', 'docs/_build/')
    session.run('sphinx-build', '-W', '-b', 'html', '-d',
                'docs/_build/doctrees', 'docs/', 'docs/_build/html/')
