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

It converts the legacy artman config file into the new format. This CLI can be
removed after all current artman users migrate to the new artman config format.
"""

from __future__ import absolute_import
from __future__ import print_function

import argparse
from collections import OrderedDict
import io
import json
import sys
import traceback
import os

import stringcase
import yaml

from artman.config.proto.config_pb2 import Artifact, Config
from google.protobuf.json_format import MessageToJson


def main(*args):
    if not args:
        args = sys.argv[1:]

    # Get to a normalized set of arguments.
    try:
        flags = _parse_args(*args)
        legacy_config = _load_legacy_config_dict(os.path.abspath(flags.config))
        new_config = _convert(legacy_config)
        _write_pb_to_yaml(new_config, flags.output)
    except Exception as e:
        traceback.print_exc(file=sys.stderr)
        sys.exit('Fail to convert `%s` due to `%s`.' % (flags.config, e))


def _parse_args(*args):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'config',
        type=str,
        help='Path to the legacy artman config')
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='If specified, the converted yaml will be stored in the given '
             'output file. Otherwise, the converter will only print out the '
             'result.')
    return parser.parse_args(args=args)


def _convert(legacy_config):
    # Compute common section
    result = Config()
    if 'common' not in legacy_config:
        sys.exit('`common` field is a required field in the legacy config.')
    legacy_common = legacy_config.get('common')
    result.common.api_name = legacy_common.get('api_name', 'unspecified')
    result.common.api_version = legacy_common.get('api_version', 'unspecified')
    result.common.organization_name = legacy_common.get(
        'organization_name', 'unspecified')

    # Python dict#get(key, default=value) doesn't well support list-type field.
    # Instead of using defaultdict, simply do the if checking here.
    if legacy_common.get('gapic_api_yaml'):
        result.common.gapic_yaml = _sanitize_repl_var(
            legacy_common.get('gapic_api_yaml')[0])
    if legacy_common.get('service_yaml'):
        result.common.service_yaml = _sanitize_repl_var(
            legacy_common.get('service_yaml')[0])
    if legacy_common.get('proto_deps'):
        result.common.proto_deps.extend(
            _compute_deps(legacy_common.get('proto_deps')))
    if legacy_common.get('proto_test_deps'):
        result.common.test_proto_deps.extend(
            _compute_deps(legacy_common.get('proto_test_deps')))
    if legacy_common.get('src_proto_path'):
        result.common.src_proto_paths.extend(
            _compute_src_proto_paths(legacy_common.get('src_proto_path')))

    artifacts = _compute_artifacts(legacy_config, legacy_common)
    # Append a gapic_config artifact.
    artifacts.append(
        Artifact(
            name='gapic_config',
            type=Artifact.GAPIC_CONFIG,
        )
    )
    result.artifacts.extend(artifacts)

    return result


def _compute_artifacts(legacy_config, legacy_common):
    result = []
    LANGS = ['java', 'python', 'php', 'ruby', 'go', 'csharp', 'nodejs']

    # Compute artifacts section
    common_git_repos = legacy_common.get('git_repos', {})

    for lang in LANGS:
        if lang not in legacy_config:
            continue
        legacy_artifact_config = legacy_config[lang]
        if legacy_artifact_config:
            artifact = Artifact(
                # Name the artifact as `{lang}_gapic`.
                name='%s_gapic' % lang,
                language=Artifact.Language.Value(lang.upper()),
            )

            if 'release_level' in legacy_artifact_config:
                artifact.release_level = Artifact.ReleaseLevel.Value(
                    legacy_artifact_config.get('release_level').upper())

            artifact.type = _compute_artifact_type(legacy_common)

            # Compute package version.
            if 'generated_package_version' in legacy_artifact_config:
                legacy_package_version = legacy_artifact_config.get(
                    'generated_package_version')
                if 'lower' in legacy_package_version:
                    artifact.package_version.grpc_dep_lower_bound = (
                        legacy_package_version.get('lower'))
                if 'upper' in legacy_package_version:
                    artifact.package_version.grpc_dep_upper_bound = (
                        legacy_package_version.get('upper'))

            # Compute publishing targets
            artifact.publish_targets.extend(_compute_publish_targets(
                legacy_artifact_config.get('git_repos', {}),
                common_git_repos))
            result.append(artifact)
    return result


def _compute_artifact_type(legacy_common):
    if legacy_common.get('packaging', '') == 'google-cloud':
        return Artifact.GAPIC_ONLY
    elif legacy_common.get('package_type', '') == 'grpc_common':
        return Artifact.GRPC_COMMON

    return Artifact.GAPIC


def _compute_publish_targets(git_repos, common_git_repos):
    # Merge the individual git_repos config with the common ones.
    for k, v in common_git_repos.items():
        if k in git_repos:
            merged_entry = v.copy()
            merged_entry.update(git_repos[k])
            git_repos[k] = merged_entry

    result = []
    for k, v in git_repos.items():
        target = Artifact.PublishTarget(
            name=k,
            location=v.get('location', ''),
            type=Artifact.PublishTarget.GITHUB,
            directory_mappings=_compute_directory_mappings(v.get('paths', []))
        )

        result.append(target)
    return result


def _compute_directory_mappings(paths):
    result = []
    for path in paths:
        mapping = {}
        if isinstance(path, str):
            mapping['dest'] = path
        else:
            if 'src' in path:
                mapping['src'] = path.get('src')
            if 'dest' in path:
                mapping['dest'] = path.get('dest')
            if 'artifact' in path:
                mapping['name'] = path.get('artifact')
        result.append(Artifact.PublishTarget.DirectoryMapping(**mapping))
    return result


def _compute_deps(proto_deps):
    result = []
    for dep in proto_deps:
        result.append(Artifact.ProtoDependency(name=dep))
    return result


def _compute_src_proto_paths(src_proto_paths):
    result = []
    for src_proto_path in src_proto_paths:
        result.append(_sanitize_repl_var(src_proto_path))
    return result


def _sanitize_repl_var(value):
    return value.replace('${REPOROOT}/', '').replace('${GOOGLEAPIS}/', '')


def _convert_json(d):
    """Convert the dict to turn all key into snake case."""
    new_d = {}
    for k, v in d.items():
        if isinstance(v, dict):
            new_d[stringcase.snakecase(k)] = _convert_json(v)
        elif isinstance(v, list):
            if isinstance(v[0], dict):
                result = []
                for d2 in v:
                    result.append(_convert_json(d2))
                new_d[stringcase.snakecase(k)] = result
            else:
                new_d[stringcase.snakecase(k)] = v
        else:
            new_d[stringcase.snakecase(k)] = v
    return new_d


def _write_pb_to_yaml(pb, output):
    # Add yaml representer so that yaml dump can dump OrderedDict. The code
    # is coming from https://stackoverflow.com/questions/16782112.
    yaml.add_representer(OrderedDict, _represent_ordereddict)

    json_obj = _order_dict(_convert_json(json.loads(MessageToJson(pb))))
    if output:
        with open(output, 'w') as outfile:
            yaml.dump(json_obj, outfile, default_flow_style=False)
        print('Check the converted yaml at %s' % output, file=sys.stdout)
    else:
        print(yaml.dump(json_obj, default_flow_style=False), file=sys.stdout)


def _represent_ordereddict(dumper, data):
    value = []
    for item_key, item_value in data.items():
        node_key = dumper.represent_data(item_key)
        node_value = dumper.represent_data(item_value)

        value.append((node_key, node_value))

    return yaml.nodes.MappingNode(u'tag:yaml.org,2002:map', value)


def _order_dict(od):
    # The whole key order is flattened which is okay for artman config because
    # the order of fields in the nested message types doesn't conflict with
    # the top-level one.
    keyorder = [
        'common', 'artifacts', 'name', 'api_name', 'api_version',
        'organization_name', 'service_yaml', 'gapic_yaml',
        'src_proto_paths', 'proto_deps', 'test_proto_deps',
        'type', 'language', 'release_level', 'package_version',
        'publish_targets', 'location', 'directory_mappings', 'src', 'dest',
        'grpc_dep_lower_bound', 'grpc_dep_upper_bound',
    ]
    res = OrderedDict()
    for k, v in sorted(od.items(), key=lambda i: keyorder.index(i[0])):
        if isinstance(v, dict):
            res[k] = _order_dict(v)
        elif isinstance(v, list):
            if isinstance(v[0], dict):
                result = []
                for d2 in v:
                    result.append(_order_dict(d2))
                res[k] = result
            else:
                res[k] = v
        else:
            res[k] = v
    return res


def _load_legacy_config_dict(path):
    with io.open(path, 'r') as yaml_file:
        return yaml.load(yaml_file)


if __name__ == "__main__":
    main()
