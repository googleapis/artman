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

"""Artman smoke tests.

It generates both grpc and gapic client libraries for Google APIs in googleapis
repo (except those being blacklisted), and fails if any generation fails.
The test currently assumes that artman and googleapis folders are under the
same parent folder.
"""

import argparse
import fnmatch
import os
import re
import subprocess
import sys

ARTMAN_CONFIG_BLACKLIST = [
    'artman_spanner_admin_instance.yaml',
    'artman_spanner_admin_database.yaml',
    'artman_bigtable_admin.yaml'
]

SUPPORTED_LANGS = ['python', 'java', 'ruby', 'nodejs', 'php', 'go', 'csharp']


def run_smoke_test(apis):
    artman_config_dir = '../googleapis/gapic/api'
    failure = []
    artman_config_list = []
    if apis:
        for api in apis.split(','):
            artman_config_list.append('artman_%s.yaml' % api)

    for root, dirs, files in os.walk(artman_config_dir):
        for f in fnmatch.filter(files, 'artman_*.yaml'):
            if f in ARTMAN_CONFIG_BLACKLIST:
                # Do not run generation tests for those in the blacklist.
                continue
            if artman_config_list and f not in artman_config_list:
                # If apis list is given, only test those in the list
                continue
            api_name = re.search('artman_(.*)\.yaml', f).group(1)
            filename = os.path.join(root, f)
            content = open(filename).read()
            for lang in SUPPORTED_LANGS:
                if '%s:' % lang in content:
                    if generate_grpc_library(filename, lang):
                        failure.append('Failed to generate grpc %s library '
                                       'for %s' % (lang, api_name))
                    if generate_gapic_library(filename, lang):
                        failure.append('Failed to generate gapic %s library '
                                       'for %s' % (lang, api_name))
    if failure:
        sys.exit('Smoke test failed:\n%s' % '\n'.join(failure))


def generate_grpc_library(artman_config, lang):
    grpc_pipeline_args = [
        'artman',
        '--config', '%s,../googleapis/gapic/lang/common.yaml' % artman_config,
        '--language', lang,
        '--pipeline', 'GrpcClientPipeline',
        '--publish', 'noop',
    ]
    return subprocess.call(grpc_pipeline_args, stdout=subprocess.PIPE)


def generate_gapic_library(artman_config, lang):
    gapic_pipeline_args = [
        'artman',
        '--config', '%s,../googleapis/gapic/lang/common.yaml' % artman_config,
        '--language', lang,
        '--publish', 'noop',
    ]
    return subprocess.call(gapic_pipeline_args, stdout=subprocess.PIPE)


def parse_args(*args):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--apis',
        default=None,
        type=str,
        help='Comma-delimited list of apis to test against. The artman config '
             'of the API must be available in googleapis/googleapis github '
             'repo in order for smoketest to run properly. If not specified, '
             'all APIs will be tested. APIs in the blacklist will not be '
             'tested.')
    return parser.parse_args(args=args)


if __name__ == "__main__":
    flags = parse_args(*sys.argv[1:])

    run_smoke_test(flags.apis)
