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

import setuptools

from pip.req import parse_requirements

requirements = [
    'gcloud>=0.10.0',
    'kazoo>=2.2.1',
    'oslo.utils>=3.4.0',
    'pyyaml>=3.11',
    'taskflow>=1.25.0,<2.0.0',
    'yapf>=0.6.2'
]

setuptools.setup(
    name='googleapis-artman',
    version='0.1.0',
    description='Google API artifact manager',
    author='Google Inc',
    author_email='googleapis-packages@google.com',
    url='https://github.com/googleapis/artman',
    license='Apache-2.0',
    install_requires=requirements,
    packages=setuptools.find_packages(),
    scripts=['execute_pipeline.py', 'start_conductor.py'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
    ]
)
