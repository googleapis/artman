#!/usr/bin/env python

# Copyright 2017 Google Inc. All Rights Reserved.
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


"""Main class to start conductor.
"""

from __future__ import absolute_import
from logging import INFO
import argparse
import logging as pylog
import sys

from artman.conductors import cloudtasks_conductor
from artman.utils.logger import logger, setup_logging

def start(*args):
    if not args:
        args = sys.argv[1:]
    flags = _parse_args(*args)
    if flags.log_local:
        pylog.basicConfig()
    cloudtasks_conductor.run(flags.queue_name)

def _parse_args(*args):
    parser = _CreateArgumentParser()
    flags = parser.parse_args(args=args)
    if not flags.queue_name:
        setup_logging(INFO)
        logger.critical('Required --queue-name flag not specified')
        sys.exit(1)
    return flags

def _CreateArgumentParser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-l", "--log-local",
        action='store_true',
        help="Log to local console.")
    parser.add_argument(
        "--queue-name",
        type=str,
        default=None,
        help="The name of task queue.")
    return parser
