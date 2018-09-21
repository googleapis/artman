#!/usr/bin/env python

# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""Setup tool for artman."""

import io
import os
import setuptools

# The following line is parsed by CI scripts (see .circleci/config.yml)
# and by release.py. Please keep the format.
current_version = '0.15.5'

cur_dir = os.path.realpath(os.path.dirname(__file__))
with io.open('%s/requirements.txt' % cur_dir) as requirements_file:
    requirements = requirements_file.read().strip().split('\n')

setuptools.setup(
    name='googleapis-artman',
    version=current_version,
    description='Google API artifact manager',
    author='Google LLC',
    author_email='googleapis-packages@google.com',
    url='https://github.com/googleapis/artman',
    license='Apache-2.0',
    install_requires=requirements,
    packages=setuptools.find_packages(),
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'artman = artman.cli.main:main',
            'configure-artman = artman.cli.configure:configure',
            'start-artman-conductor = artman.cli.conductor:start',
        ],
    },
    scripts=[
        'test/smoketest_artman.py',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ]
)
