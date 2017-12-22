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

from artman.config.proto.config_pb2 import Artifact
from artman.utils.logger import logger


def convert_to_legacy_config_dict(artifact_config, root_dir, output_dir):
    common = {}
    common['api_name'] = artifact_config.api_name
    common['api_version'] = artifact_config.api_version
    common['organization_name'] = artifact_config.organization_name
    if artifact_config.service_yaml:
        common['service_yaml'] = [artifact_config.service_yaml]
    else:
        common['service_yaml'] = []
    if artifact_config.gapic_yaml:
        common['gapic_api_yaml'] = [artifact_config.gapic_yaml]
    else:
        common['gapic_api_yaml'] = []
    common['src_proto_path'], excluded_proto_path = _calculate_proto_paths(
        _repeated_proto3_field_to_list(
            artifact_config.src_proto_paths))
    if excluded_proto_path:
        common['excluded_proto_path'] = excluded_proto_path
    common['import_proto_path'] = [root_dir]
    common['output_dir'] = output_dir

    legacy_proto_deps, legacy_test_proto_deps, desc_proto_paths = (
        _proto_deps_to_legacy_configs(artifact_config.proto_deps,
                                      artifact_config.test_proto_deps))
    common['proto_deps'] = legacy_proto_deps
    common['proto_test_deps'] = legacy_test_proto_deps
    common['desc_proto_path'] = desc_proto_paths

    package_type = 'grpc_client'  # default package_type
    packaging = 'single-artifact'  # default packaing
    if artifact_config.type == Artifact.GRPC_COMMON:
        package_type = 'grpc_common'
        # For backward-compatibility.
        # TODO(ethanbao): Should not restrict to google-cloud packaging.
        packaging = 'google-cloud'
    elif artifact_config.type == Artifact.GAPIC_ONLY:
        packaging = 'google-cloud'

    common['packaging'] = packaging
    common['package_type'] = package_type

    result = {}
    result['common'] = common

    if artifact_config.type == Artifact.GAPIC_CONFIG:
        # Early return if the artifact type is GAPIC_CONFIG
        return result

    language = Artifact.Language.Name(
        artifact_config.language).lower()
    language_config_dict = {}
    rel_gapic_code_dir = _calculate_rel_gapic_output_dir(
        language, artifact_config.api_name, artifact_config.api_version)
    language_config_dict['gapic_code_dir'] = os.path.join(
        output_dir, rel_gapic_code_dir)
    language_config_dict['git_repos'] = _calculate_git_repos_config(
        artifact_config, output_dir)
    if artifact_config.release_level != Artifact.RELEASE_LEVEL_UNSPECIFIED:
        language_config_dict['release_level'] = (
            Artifact.ReleaseLevel.Name(
                artifact_config.release_level).lower())

    # Convert package version configuration.
    pv = artifact_config.package_version
    if pv:
        package_version_dict = {}
        if pv.grpc_dep_lower_bound:
            package_version_dict['lower'] = pv.grpc_dep_lower_bound
        if pv.grpc_dep_upper_bound:
            package_version_dict['upper'] = pv.grpc_dep_upper_bound
        if package_version_dict.keys():
            language_config_dict['generated_package_version'] = (
                package_version_dict)

    result[language] = language_config_dict
    return result


def _repeated_proto3_field_to_list(field):
    """Convert a proto3 repeated field to list.

    Repeated fields are represented as an object that acts like a Python
    sequence. It cannot be assigned to a list type variable. Therefore, doing
    the conversion manually.
    """
    result = []
    for item in field:
        result.append(item)
    return result


def _proto_deps_to_legacy_configs(proto_deps, test_proto_deps):
    legacy_proto_deps, legacy_test_proto_deps, desc_proto_paths = [], [], []
    for dep in proto_deps:
        legacy_proto_deps.append(dep.name)
        # TODO(ethanbao): This is way too magical, and need to figure out a
        # better way one option is to formalize the ProtoDependency with more
        # fields and make current gapic/packaging/dependencies.yaml into that
        # ProtoDependency type, which will include the real file path.
        if dep.name == 'google-iam-v1':
            desc_proto_paths.append('${GOOGLEAPIS}/google/iam/v1')
    for test_dep in test_proto_deps:
        legacy_test_proto_deps.append(test_dep.name)
    return legacy_proto_deps, legacy_test_proto_deps, desc_proto_paths


def _calculate_rel_gapic_output_dir(language, api_name, api_version):
    """Calculate the gapic output dir relative to the specified output_dir.

    TODO(ethanbao): This part can become part of normalization step when gapic
    ouput dir becomes configurable. This logic doesn't work for non-cloud.
    """
    if language == 'java':
        return 'java/google-cloud-%s' % api_name
    elif language == 'csharp':
        return 'csharp/google-cloud-%s' % api_name
    elif language == 'go':
        return 'gapi-cloud-%s-go' % api_name
    elif language == 'nodejs':
        return 'js/%s-%s' % (api_name, api_version)
    elif language == 'php':
        return 'google-php-cloud-%s-%s' % (api_name, api_version)
    elif language == 'python':
        return 'python/%s-%s' % (api_name, api_version)
    elif language == 'ruby':
        api_name = api_name.replace('-', '_')
        return 'ruby/google-cloud-ruby/google-cloud-%s' % api_name

    raise ValueError('Language `%s` is not currently supported.' % language)


def _calculate_git_repos_config(artifact_config, output_dir):
    result = {}
    for target in artifact_config.publish_targets:
        if not target.type == Artifact.PublishTarget.GITHUB:
            continue
        item = {}
        item['location'] = target.location
        paths = []
        for map_entry in target.directory_mappings:
            path = {}
            if map_entry.src:
                path['src'] = os.path.join(output_dir, map_entry.src)
            if map_entry.dest:
                path['dest'] = map_entry.dest
            if map_entry.name:
                path['artifact'] = map_entry.name
            if (map_entry.name not in ['grpc', 'proto']
                or artifact_config.language == Artifact.JAVA):
              paths.append(path)
            else:
              logger.warning('"%s" publishing artifact type is only used in '
                             'Java. Ignore that config.' % map_entry.name)
        item['paths'] = paths
        result[target.name] = item
    return result


def _calculate_proto_paths(proto_paths):
    src_proto_path, excluded_proto_path = [], []
    for proto_path in proto_paths:
        if proto_path.startswith('-'):
            excluded_proto_path.append(proto_path[1:])
        else:
            src_proto_path.append(proto_path)
    return src_proto_path, excluded_proto_path
