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

import os
import fnmatch
import subprocess
import sys

ARTMAN_CONFIG_BLACKLIST= [
    'artman_spanner_admin_instance.yaml',
    'artman_spanner_admin_database.yaml',
    'artman_bigtable_admin.yaml'
]

# Not ready to test Go and Csharp yet.
SUPPORTED_LANGS = ['python', 'java', 'ruby', 'nodejs', 'php', 'go']

def run_smoke_test():
    artman_config_dir = '../googleapis/gapic/api'
    failure = []
    for root, dirs, files in os.walk(artman_config_dir):
        for f in fnmatch.filter(files, 'artman_*.yaml'):
            if f in ARTMAN_CONFIG_BLACKLIST:
                # Do not run generation tests for those in the blacklist.
                continue
            filename = os.path.join(root, f)
            content = open(filename).read()
            for lang in SUPPORTED_LANGS:
                if '%s:' % lang in content:
                    if generate_grpc_library(filename, lang):
                        failure.append('Failed to generate grpc %s library '
                                       'using %s config.' % (lang, filename))
                    if generate_gapic_library(filename, lang):
                        failure.append('Failed to generate gapic %s library '
                                       'using %s config.' % (lang, filename))
    if failure:
        sys.exit('Smoke test failed with %s' % ' '.join(failure))

def generate_grpc_library(artman_config, lang):
    grpc_pipeline_args = [
        'artman',
        '--user-config', 'test/artman_user_config_in_smoketest.yaml',
        '--config', '%s,../googleapis/gapic/lang/common.yaml' % artman_config,
        '--language', lang,
        '--pipeline', 'GrpcClientPipeline',
        '--publish', 'noop',
    ]
    return subprocess.call(grpc_pipeline_args, stdout=subprocess.PIPE)

def generate_gapic_library(artman_config, lang):
    gapic_pipeline_args = [
        'artman',
        '--user-config', 'test/artman_user_config_in_smoketest.yaml',
        '--config', '%s,../googleapis/gapic/lang/common.yaml' % artman_config,
        '--language', lang,
        '--publish', 'noop',
    ]
    return subprocess.call(gapic_pipeline_args, stdout=subprocess.PIPE)

if __name__ == "__main__":
    run_smoke_test()
