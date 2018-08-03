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

"""Artman config converter.

It converts the new artman config file into the legacy format so that current
artman code can work with both legacy and new artman config file. We will phase
out legacy artman config yamls and make artman code read the configuration from
the new artman config. Once that is done, this converter can be removed.
"""

from __future__ import absolute_import
import os
from protobuf_to_dict import protobuf_to_dict

from artman.config.proto.config_pb2 import Artifact
from artman.utils.logger import logger


def convert_to_legacy_config_dict(artifact_config, root_dir, output_dir):
    artifact_config_dict = protobuf_to_dict(artifact_config)
    common = {}
    common['api_name'] = artifact_config.api_name
    common['api_version'] = artifact_config.api_version
    common['organization_name'] = artifact_config.organization_name
    common['service_yaml'] = artifact_config.service_yaml
    common['gapic_yaml'] = artifact_config.gapic_yaml
    src_proto_paths = artifact_config_dict.get('src_proto_paths', [])
    common['src_proto_path'], excluded_proto_path = _calculate_proto_paths(src_proto_paths)
    if excluded_proto_path:
        common['excluded_proto_path'] = excluded_proto_path
    common['import_proto_path'] = [root_dir]
    common['output_dir'] = output_dir
    common['proto_deps'] = []
    if 'proto_deps' in artifact_config_dict:
        common['proto_deps'] = artifact_config_dict['proto_deps']
    if 'test_proto_deps' in artifact_config_dict:
        common['test_proto_deps'] = artifact_config_dict['test_proto_deps']
    common['artifact_type'] = Artifact.Type.Name(artifact_config.type)

    result = {}
    result['common'] = common

    if artifact_config.type == Artifact.GAPIC_CONFIG\
        or artifact_config.type == Artifact.DISCOGAPIC_CONFIG:
        # Early return if the artifact type is GAPIC_CONFIG or DISCOGAPIC_CONFIG
        return result

    language = Artifact.Language.Name(
        artifact_config.language).lower()
    language_config_dict = {}
    rel_gapic_code_dir = _calculate_rel_gapic_output_dir(
        language, artifact_config.api_name, artifact_config.api_version)
    language_config_dict['gapic_code_dir'] = os.path.join(
        output_dir, rel_gapic_code_dir)
    if artifact_config.release_level != Artifact.RELEASE_LEVEL_UNSPECIFIED:
        language_config_dict['release_level'] = (
            Artifact.ReleaseLevel.Name(
                artifact_config.release_level).lower())

    result[language] = language_config_dict
    return result


def _calculate_rel_gapic_output_dir(language, api_name, api_version):
    """Calculate the gapic output dir relative to the specified output_dir.

    TODO(ethanbao): This part can become part of normalization step when gapic
    ouput dir becomes configurable. This logic doesn't work for non-cloud.
    """
    if language == 'java':
        return 'java/gapic-google-cloud-%s-%s' % (api_name, api_version)
    elif language == 'csharp':
        return 'csharp/google-cloud-%s' % api_name
    elif language == 'go':
        return 'gapi-cloud-%s-go' % api_name
    elif language == 'nodejs':
        return 'js/%s-%s' % (api_name, api_version)
    elif language == 'php':
        return 'php/google-cloud-%s-%s' % (api_name, api_version)
    elif language == 'python':
        return 'python/%s-%s' % (api_name, api_version)
    elif language == 'ruby':
        api_name = api_name.replace('-', '_')
        return 'ruby/google-cloud-ruby/google-cloud-%s' % api_name

    raise ValueError('Language `%s` is not currently supported.' % language)

def _calculate_proto_paths(proto_paths):
    src_proto_path, excluded_proto_path = [], []
    for proto_path in proto_paths:
        if proto_path.startswith('-'):
            excluded_proto_path.append(proto_path[1:])
        else:
            src_proto_path.append(proto_path)
    return src_proto_path, excluded_proto_path
