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

It generates GAPIC client libraries for Google APIs in googleapis
repo. The test will fails if any generation fails unless its artman yaml file
is on the whitelist.
"""

import argparse
import glob
import json
import logging
import os
import re
import subprocess
import sys
import yaml

from google.protobuf import json_format

from artman.config.proto import config_pb2

# Generation failure of artifact on the whitelist won't be counted as failure
# but warning. It is defined at artifact level, and one can use regex to
# whitelist the whole API or whole folder.
WHITELIST = [
    # The two configs below are failing: https://github.com/googleapis/artman/issues/483
    'python_gapic@google/devtools/containeranalysis/artman_containeranalysis_v1beta1.yaml',
    'ruby_gapic@google/devtools/containeranalysis/artman_containeranalysis_v1beta1.yaml',

    'gapic_config@google/bigtable/admin/artman_bigtableadmin.yaml',
    'nodejs_gapic@google/cloud/videointelligence/artman_videointelligence_v1.yaml',
    # TODO(ethanbao): Figure out the rootcause
    'java_gapic@google/cloud/dialogflow/artman_dialogflow_v2beta1_java.yaml',
    # TODO(michaelbausor): Remove once the php_gapic generation works.
    'php_gapic@google/cloud/dialogflow/artman_dialogflow_v2beta1.yaml',
    '.+@google/api/servicemanagement/artman_servicemanagement_v1.yaml',
    '.+@google/devtools/remoteworkers/v1test2/artman_remoteworkers.yaml',

    # https://github.com/googleapis/gapic-generator/issues/2265
    'python_gapic@google/iam/credentials/artman_iamcredentials_v1.yaml',

    # TODO(pongad): talk to the API owners
    '(?:python|php)_gapic@google/api/expr/artman_cel.yaml',
]

logger = logging.getLogger('smoketest')
logger.setLevel(logging.INFO)


def run_smoke_test(root_dir, log):
    log_file = _setup_logger(log)
    failure = []
    success = []
    known_fail = []
    for artman_yaml_path in glob.glob('%s/google/**/artman_*.yaml' % root_dir,
                                      recursive=True):
        artman_config = _parse(artman_yaml_path)
        # Reorder the artifacts by moving the gapic_config artifact to the end.
        # Otherwise, the following GAPIC library generation is going to use the
        # newly-generated GAPIC config instead of the one in github, leading to
        # false negative and false positive in the test result.
        artifacts = sorted(
            artman_config.artifacts,
            key=lambda a: config_pb2.Artifact.GAPIC_CONFIG == a.type)

        for artifact in artifacts:
            logger.info('Start artifact generation for %s of %s'
                        % (artifact.name, artman_yaml_path))
            if _generate_artifact(artman_yaml_path,
                                  artifact.name,
                                  root_dir,
                                  log_file):
                msg = 'Failed to generate %s of %s.' % (
                    artifact.name, artman_yaml_path)
                if _is_whitelisted(artman_yaml_path, root_dir, artifact.name):
                    known_fail.append(msg)
                else:
                    failure.append(msg)
            else:
                msg = 'Succeded to generate %s of %s.' % (
                    artifact.name, artman_yaml_path)
                success.append(msg)
            logger.info(msg)
    logger.info('================ Smoketest summary ================')
    logger.info('Success:')
    for msg in success:
        logger.info(msg)

    if known_fail:
        logger.info('Known Whitelisted Failures:')
        for msg in known_fail:
            logger.info(msg)

    if failure:
        logger.info('Failure:')
        for msg in failure:
            logger.error(msg)
        sys.exit('Smoke test failed.')


def _parse(artman_yaml_path):
    """Parse artman yaml config into corresponding protobuf."""
    with open(artman_yaml_path, 'r') as f:
        # Convert yaml into json file as protobuf python load support parsing
        # of protobuf in json or text format, not yaml.
        artman_config_json_string = json.dumps(yaml.load(f))
    config_pb = config_pb2.Config()
    json_format.Parse(artman_config_json_string, config_pb)

    return config_pb


def _generate_artifact(artman_config, artifact_name, root_dir, log_file):
    with open(log_file, 'a') as log:
        grpc_pipeline_args = [
            'artman',
            '--local',
            '--verbose',
            '--config', artman_config,
            '--root-dir', root_dir,
            'generate', artifact_name
        ]
        return subprocess.call(grpc_pipeline_args, stdout=log, stderr=log)


def _is_whitelisted(artman_yaml_path, root_dir, artifact_name):
    artifact = '%s@%s' % (artifact_name,
                          os.path.relpath(artman_yaml_path, root_dir))
    for whitelist in WHITELIST:
        if re.match(whitelist, artifact):
            return True
    return False


def parse_args(*args):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--root-dir',
        default='/googleapis',
        type=str,
        help='Specify where googleapis local repo lives.')
    parser.add_argument(
        '--log',
        default='/tmp/smoketest.log',
        type=str,
        help='Specify where smoketest log should be stored.')
    return parser.parse_args(args=args)


def _setup_logger(log_file):
    """Setup logger with a logging FileHandler."""
    log_file_handler = logging.FileHandler(log_file, mode='a+')
    logger.addHandler(log_file_handler)
    logger.addHandler(logging.StreamHandler())
    return log_file


if __name__ == '__main__':
    flags = parse_args(*sys.argv[1:])

    run_smoke_test(os.path.abspath(flags.root_dir), os.path.abspath(flags.log))
