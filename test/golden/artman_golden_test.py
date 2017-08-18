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

"""Artman golden tests.

It runs GAPIC generation against the golden input data, can then compare the
output layout with the expected output. This helps to capture unexpected GAPIC
output layout change caused by either by artman, toolkit or other runtime
dependency.
"""

import io
import os
import subprocess

import pytest


def test_library_example(googleapis_dir):
    # TODO(ethanbao): Templatize this test so that we can run more golden tests.
    golden_dir = os.path.dirname(os.path.realpath(__file__))
    output_dir = '/output/new'

    if not googleapis_dir:
        pytest.skip(
            'Skip the golden test as the --googleapis-dir flag is not set.')

    with open(os.path.join(golden_dir, 'library_example.golden')) as f:
        expected = set()
        for line in f.read().splitlines():
            line = line.strip()
            if line and not line.startswith('#'):
                expected.add(line)

    for artifact in ['python', 'java', 'ruby', 'nodejs', 'php', 'go', 'csharp']:
        generate_gapic_library(golden_dir, googleapis_dir, output_dir, artifact)


    actual = []
    for root, subdirs, files in os.walk(output_dir):
        for f in files:
            actual.append(os.path.join(root, f)[len(output_dir):])

    # Store the actual output relative to the working directory.
    actual_output_file = os.path.join(
        golden_dir, 'actual_library_example.golden')
    with io.open(actual_output_file, 'w+') as output:
        for item in sorted(actual):
            output.write('%s\n' % item)
    assert expected == set(actual), \
        "Check the actual output at %s" % actual_output_file

def test_library_example_with_legacy_syntax(googleapis_dir):
    # TODO(cbao): Remove after the old artman config and CLI get phased out.`
    golden_dir = os.path.dirname(os.path.realpath(__file__))
    if not googleapis_dir:
        pytest.skip(
            'Skip the golden test as the --googleapis-dir flag is not set.')

    # It is intended to use the same expected golden output so that we know
    # the new artman config is compatible with the old one from the output
    # perspective.
    # Note: this test doesn't test publishing feature.
    with open(os.path.join(golden_dir, 'library_example.golden')) as f:
        expected = set()
        for line in f.read().splitlines():
            line = line.strip()
            if line and not line.startswith('#'):
                expected.add(line)

    for lang in ['python', 'java', 'ruby', 'nodejs', 'php', 'go', 'csharp']:
        generate_gapic_library_legacy(golden_dir, googleapis_dir, lang)

    output_dir = '/output/legacy'
    actual = []
    for root, subdirs, files in os.walk(output_dir):
        for f in files:
            actual.append(os.path.join(root, f)[len(output_dir):])

    # Store the actual output relative to the working directory.
    actual_output_file = os.path.join(
        golden_dir, 'actual_library_example_legacy.golden')
    with io.open(actual_output_file, 'w+') as output:
        for item in sorted(actual):
            output.write('%s\n' % item)
    assert expected == set(actual), \
        "Check the actual output at %s" % actual_output_file

def generate_gapic_library(golden_dir, googleapis_dir, output_dir, artifact_id):
    gapic_pipeline_args = [
        'artman2',
        '--config', '%s/artman_library_example_new.yaml' % golden_dir,
        '--local',
        '--input-dir', googleapis_dir,
        '--output-dir', output_dir,
        'generate',
        artifact_id,
    ]
    subprocess.check_call(gapic_pipeline_args, stdout=subprocess.PIPE)

def generate_gapic_library_legacy(golden_dir, googleapis_dir, lang):
    gapic_pipeline_args = [
        'artman',
        '--config', '%s/artman_library_example.yaml,'
                    '%s/gapic/lang/%s.yaml'
                    % (golden_dir, googleapis_dir,
                      'doc' if lang == 'ruby' else 'common'),
        '--googleapis', googleapis_dir,
        '--language', lang,
        '--publish', 'noop',
    ]
    subprocess.check_call(gapic_pipeline_args, stdout=subprocess.PIPE)
