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

"""Artman config reader that parses, validates and normalizes the passed artman
config.
"""

from __future__ import absolute_import
import json
import os
import yaml

from google.protobuf import json_format

from artman.config.proto import config_pb2


def load_artifact_config(artman_config_path, artifact_name, input_dir):
    artman_config = _read_artman_config(artman_config_path)
    artifact_config = config_pb2.Artifact()
    artifact_config.CopyFrom(artman_config.common)
    valid_values = []
    for artifact in artman_config.artifacts:
        valid_values.append(artifact.name)
        if artifact.name == artifact_name:
            artifact_config.MergeFrom(artifact)
            _validate_artifact_config(artifact_config)
            return _normalize_artifact_config(artifact_config, input_dir)

    raise ValueError(
        'No artifact with `%s` configured in artman yaml. Valid values are %s'
        % (artifact_name, valid_values))


def _read_artman_config(artman_yaml_path):
    """Parse and return artman config after validation and normalization."""
    artman_config = _parse(artman_yaml_path)
    validation_result = _validate_artman_config(artman_config)
    if validation_result:
        raise ValueError(validation_result)
    else:
        return artman_config


def _parse(artman_yaml_path):
    """Parse artman yaml config into corresponding protobuf."""
    with open(artman_yaml_path, 'r') as f:
        # Convert yaml into json file as protobuf python load support paring of
        # protobuf in json or text format, not yaml.
        artman_config_json_string = json.dumps(yaml.load(f))
    config_pb = config_pb2.Config()
    json_format.Parse(artman_config_json_string, config_pb)

    return config_pb


def _validate_artman_config(config_pb):
    """ Validate the parsed config_pb.

    Currently, it checkes the uniqueness of the artifact name, and uniqieuness
    of publishing target name in each artifact. Plus, it makes sure the
    specified configuration or other input file or folder exists.
    """
    artifacts = set()
    for artifact in config_pb.artifacts:
        targets = set()
        if artifact.name in artifacts:
            return ('artifact `%s` has been configured twice, please rename.' %
                    artifact.name)
        artifacts.add(artifact.name)
        for target in artifact.publish_targets:
            if target.name in targets:
                return ('publish target `%s` in artifact `%s` has been '
                        'configured twice, please rename.' %
                        (target.name, artifact.name))
            targets.add(target.name)

    return None


def _validate_artifact_config(artifact_config):
    # TODO(ethanbao) Validate input files, in which we disallow ${GOOGLEAPIS}
    # syntax and the file or folder must exist.
    pass


def _normalize_artifact_config(artifact_config, input_dir):
    """Normalize the config protobuf based on flags passed from command line.

    Note: we are not normalizing output folders because they are no longer
    configurable, and the output folder calculation now happens in converter.
    Once the individual GAPIC output folder becomes configurable, that folder
    name calculation logic should be moved from converter into this method.
    """
    # Normalize the input file or folder by prefixing with input_dir if needed.
    artifact_config.service_yaml = _normalize_path(
        artifact_config.service_yaml, input_dir)

    artifact_config.gapic_yaml = _normalize_path(
        artifact_config.gapic_yaml, input_dir)

    if not artifact_config.import_proto_path:
        artifact_config.import_proto_path[:] = [input_dir]
    else:
        normalized_import_proto_path = []
        for import_proto_path in artifact_config.import_proto_path:
            normalized_import_proto_path.append(
                _normalize_path(import_proto_path, input_dir))

        artifact_config.import_proto_path[:] = normalized_import_proto_path

    normalized_src_proto_paths = []
    for src_proto_path in artifact_config.src_proto_paths:
        if src_proto_path.startswith('-'):
            # Retain the exclusion mark "-" as the prefix of the normalized path
            normalized_src_proto_paths.append(
                '-%s' % _normalize_path(src_proto_path[1:], input_dir))
        else:
            normalized_src_proto_paths.append(
                _normalize_path(src_proto_path, input_dir))
    artifact_config.src_proto_paths[:] = normalized_src_proto_paths

    return artifact_config

def _normalize_path(path, prefix):
  return path if os.path.isabs(path) else os.path.join(prefix, path)
