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


@nox.session
@nox.parametrize('python_version', ['2.7', '3.4', '3.5', '3.6'])
def unit_tests(session, python_version):
    """Run the unit test suite."""

    # Run unit tests against all supported versions of Python.
    session.interpreter = 'python{}'.format(python_version)

    # Install all test dependencies, then install this package in-place.
    session.install('mock', 'pytest', 'pytest-cov', 'pyfakefs')
    session.install('-e', '.')

    # Run py.test against the unit tests.
    session.run('py.test', '-rxs', '--cov', '--cov-append', '--cov-report=')


@nox.session
def lint(session):
    """Run the linter."""
    session.interpreter = 'python3.6'
    session.install('flake8')
    session.run('flake8', '--max-complexity=8', 'artman',
                '--exclude=test/output', 'test')


@nox.session
def coverage(session):
    """Provide a coverage report."""
    session.interpreter = 'python3.6'
    session.install('coverage')
    try:
        # session.run('coverage', 'report')
        session.run('coverage', 'html')
    finally:
        session.run('coverage', 'erase')
