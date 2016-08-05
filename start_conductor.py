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


"""Main class to start conductor.
"""

import argparse

from pipeline.conductors import gapic_conductor


def main():
  jobboard_name = _parse_args()
  gapic_conductor.run(jobboard_name)

def _parse_args():
  parser = _CreateArgumentParser()
  flags = parser.parse_args()
  return flags.jobboard_name.lower()

def _CreateArgumentParser():
  parser = argparse.ArgumentParser()
  parser.add_argument(
      "--jobboard_name",
      type=str,
      default="remote",
      help="The name of the jobboard to monitor.")
  return parser

if __name__ == '__main__':
  main()
