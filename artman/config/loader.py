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
import io
import json
import os

from google.protobuf import json_format
import yaml

from artman.config.proto.config_pb2 import Artifact, Config
from artman.config.proto.user_config_pb2 import UserConfig
from artman.utils.logger import logger

# Error messages
CONFIG_NOT_FOUND_ERROR_MESSAGE_FORMAT = (
    'Artman YAML cannot be found at `%s`. Please check the file location.')
# TODO(ethanbao): Add a reference link once Artman schema spec is publicly
# available.
INVALID_CONFIG_ERROR_MESSAGE_FORMAT = 'Artman YAML %s is invalid.'
INVALID_USER_CONFIG_ERROR_MESSAGE_FORMAT = 'Artman user YAML %s is invalid.'


ARTIFACT_MAPPING = {
    'java_proto': {'language': 'JAVA', 'type': 'PROTOBUF'},
    'java_grpc': {'language': 'JAVA', 'type': 'GRPC'},
    'ruby_grpc': {'language': 'RUBY', 'type': 'GRPC'},
    'python_grpc': {'language': 'PYTHON', 'type': 'GRPC'},
    'java_gapic': {'language': 'JAVA', 'type': 'GAPIC'},
    'java_discogapic': {'language': 'JAVA', 'type': 'DISCOGAPIC'},
    'java_gapic_only': {'language': 'JAVA', 'type': 'GAPIC_ONLY'},
    'python_gapic': {'language': 'PYTHON', 'type': 'GAPIC'},
    'nodejs_gapic': {'language': 'NODEJS', 'type': 'GAPIC'},
    'php_gapic': {'language': 'PHP', 'type': 'GAPIC'},
    'go_gapic': {'language': 'GO', 'type': 'GAPIC'},
    'ruby_gapic': {'language': 'RUBY', 'type': 'GAPIC'},
    'csharp_gapic': {'language': 'CSHARP', 'type': 'GAPIC'},
    'gapic_config': {'type': 'GAPIC_CONFIG'},
    'discogapic_config': {'type': 'DISCOGAPIC_CONFIG'},
    'php_grpc': {'language': 'JAVA', 'type': 'GRPC'},
}


def load_artifact_config(artman_config_path, artifact_name, aspect=None):
    artman_config = _read_artman_config(artman_config_path)
    artifact_config = Artifact()
    artifact_config.CopyFrom(artman_config.common)

    if artifact_name not in ARTIFACT_MAPPING:
        raise ValueError(
            'Artifact type `%s` not supported. Valid values are %s'
            % (artifact_name, ARTIFACT_MAPPING.keys()))
    loaded_artifact = Artifact(**ARTIFACT_MAPPING[artifact_name])

    for artifact in artman_config.artifacts:
        if artifact.name == artifact_name:
            loaded_artifact.MergeFrom(artifact)
            break

    if aspect:
        loaded_artifact.aspect = Artifact.Aspect.Value(aspect)

    artifact_config.MergeFrom(loaded_artifact)
    _validate_artifact_config(artifact_config)
    return _normalize_artifact_config(
        artifact_config, artman_config_path)


def read_user_config(artman_user_config_path):
    """Parse and return artman config"""
    config_pb = UserConfig()
    artman_user_config_path = os.path.expanduser(artman_user_config_path)
    if not os.path.isfile(artman_user_config_path):
      logger.warn(
          'No artman user config defined. Use the default one for this '
          'execution. Run `configure-artman` to set up user config.')
      return config_pb

    try:
        with io.open(artman_user_config_path, 'r', encoding='UTF-8') as f:
            # Convert yaml into json file as protobuf python load support
            # parsing of protobuf in json or text format, not yaml.
            json_string = json.dumps(yaml.load(f))
        json_format.Parse(json_string, config_pb)
    except (json_format.ParseError, yaml.parser.ParserError):
        logger.error(INVALID_USER_CONFIG_ERROR_MESSAGE_FORMAT % artman_user_config_path)
        raise

    return config_pb

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
    if not os.path.exists(artman_yaml_path):
        raise ValueError(CONFIG_NOT_FOUND_ERROR_MESSAGE_FORMAT % artman_yaml_path)

    try:
        with io.open(artman_yaml_path, 'r', encoding='UTF-8') as f:
            # Convert yaml into json file as protobuf python load support paring of
            # protobuf in json or text format, not yaml.
            artman_config_json_string = json.dumps(yaml.load(f))
        config_pb = Config()
        json_format.Parse(artman_config_json_string, config_pb)
    except (json_format.ParseError, yaml.parser.ParserError):
        logger.error(INVALID_CONFIG_ERROR_MESSAGE_FORMAT % artman_yaml_path)
        raise

    return config_pb


def _validate_artman_config(config_pb):
    """ Validate the parsed config_pb.

    Currently, it checkes the uniqueness of the artifact name, and uniqieuness
    of publishing target name in each artifact. Plus, it makes sure the
    specified configuration or other input file or folder exists.
    """
    artifacts = set()
    for artifact in config_pb.artifacts:
        if artifact.name in artifacts:
            return ('artifact `%s` has been configured twice, please rename.' %
                    artifact.name)
        artifacts.add(artifact.name)

    return None


def _validate_artifact_config(artifact_config):
    if (artifact_config.language == Artifact.NODEJS and
            artifact_config.type == Artifact.GRPC):
        raise ValueError('GRPC artifact type is invalid for NodeJS.')


def _normalize_artifact_config(artifact_config, artman_config_path):
    """Normalize the config protobuf based on flags passed from command line.

    Note: we are not normalizing output folders because they are no longer
    configurable, and the output folder calculation now happens in converter.
    Once the individual GAPIC output folder becomes configurable, that folder
    name calculation logic should be moved from converter into this method.
    """
    # Normalize the input file or folder by concatenating relative path with
    # the folder of artman config yaml.
    if artifact_config.service_yaml:
        artifact_config.service_yaml = _normalize_path(
            artifact_config.service_yaml, artman_config_path, 'service_yaml')

    if artifact_config.gapic_yaml:
        artifact_config.gapic_yaml = _normalize_path(
            artifact_config.gapic_yaml, artman_config_path, 'gapic_yaml')

    normalized_src_proto_paths = []
    for src_proto_path in artifact_config.src_proto_paths:
        if src_proto_path.startswith('-'):
            # Retain the exclusion mark "-" as the prefix of the normalized path
            normalized_src_proto_paths.append(
                '-%s' % _normalize_path(src_proto_path[1:],
                                        artman_config_path,
                                        'src_proto_paths'))
        else:
            normalized_src_proto_paths.append(
                _normalize_path(src_proto_path,
                                artman_config_path,
                                'src_proto_paths'))
    artifact_config.src_proto_paths[:] = normalized_src_proto_paths

    return artifact_config


def _normalize_path(path, artman_config_path, field):
    if path.startswith('..') or '/..' in path:
        raise ValueError(
            '".." is disallowed in `%s` field of `%s`. Please use either a '
            'path relative to `%s` (preferred), or an absolute path.'
            % (field, artman_config_path,
               os.path.dirname(artman_config_path)))
    if os.path.isabs(path):
        return path
    else:
        return os.path.join(os.path.dirname(artman_config_path), path)
