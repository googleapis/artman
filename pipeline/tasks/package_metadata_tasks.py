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

"""Tasks related to package metadata"""

import os
import yaml

from pipeline.tasks import task_base
from pipeline.utils import task_utils


class PackageMetadataConfigGenTask(task_base.TaskBase):
    """Generates package metadata config"""
    default_provides = 'package_metadata_yaml'

    def execute(self, api_name, api_version, organization_name, output_dir,
                package_dependencies_yaml, package_defaults_yaml, repo_root,
                src_proto_path):
        googleapis_dir = os.path.join(repo_root, 'googleapis')
        googleapis_path = os.path.commonprefix(
            [os.path.relpath(p, googleapis_dir) for p in src_proto_path])
        api_full_name = task_utils.api_full_name(
            api_name, api_version, organization_name)

        with open(package_dependencies_yaml) as dep_file:
            package_dependencies = yaml.load(dep_file)
        with open(package_defaults_yaml) as dep_file:
            package_defaults = yaml.load(dep_file)

        config = {
            'short_name': api_name,
            'major_version': api_version,
            'proto_path': googleapis_path,
            'author': package_defaults['author'],
            'email': package_defaults['email'],
            'homepage': package_defaults['homepage'],
            'license': package_defaults['license'],
            'package_name': {
                'default': api_full_name
            },
            # TODO (geigerj): replace hardcoded value once
            #   GrpcPackageMetadataGen is using new config. Instead,
            #   change dependencies.yaml to use dict, and use
            #
            # 'package_version': self._construct_lang_version_dict(
            #     package_defaults['semver']),
            'package_version': {
                'python': {
                    'lower': '0.14.0',
                    'upper': '0.15.0dev'
                }},
            'gax_version': self._construct_lang_version_dict(
                package_dependencies['gax']),
            'proto_version': self._construct_lang_version_dict(
                package_dependencies['protobuf']),
            'common_protos_version': self._construct_lang_version_dict(
                package_dependencies['googleapis_common_protos']),
            'auth_version': self._construct_lang_version_dict(
                package_dependencies['auth'])
        }

        package_metadata_config = os.path.join(
            output_dir, api_full_name + '_package.yaml')
        with open(package_metadata_config, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)

        return package_metadata_config

    # TODO(geigerj): modify old packman configs to use terminology consisitent
    #   with new bounds ("lower"/"upper" version bounds)
    def _construct_lang_version_dict(self, input_config):
        output_config = {}
        for lang in input_config:
            try:
                output_config[lang] = {
                    'lower': input_config[lang]['version'],
                    'upper': input_config[lang]['next_version']
                }
            except KeyError:
                raise KeyError(
                    'Invalid package config format: "{}", {}'.format(
                        lang, input_config[lang]))
        return output_config

    # Separated so that this can be mocked for testing
    def _write_yaml(self, config_dict, dest):
        with open(dest, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False)


class GrpcPackageMetadataGenTask(task_base.TaskBase):
    default_provides = 'package_dir'

    def execute(self, api_name, api_version, organization_name, toolkit_path,
                descriptor_set, src_proto_path, service_yaml,
                intermediate_package_dir, output_dir,
                package_dependencies_yaml, package_defaults_yaml, language,
                repo_root):
        service_args = ['--service_yaml=' + os.path.abspath(yaml)
                        for yaml in service_yaml]

        # The path under googleapis linked to in the package metadata is the
        # last common ancestor of all source proto paths.
        # TODO (geigerj): remove this and switch to using PackageMetadataConfig
        googleapis_dir = self._googleapis_dir(repo_root)
        googleapis_path = os.path.commonprefix(
            [os.path.relpath(p, googleapis_dir) for p in src_proto_path])

        api_full_name = task_utils.api_full_name(
            api_name, api_version, organization_name)
        pkg_dir = os.path.join(output_dir, 'python', 'grpc-' + api_full_name)

        args = [
            '--descriptor_set=' + os.path.abspath(descriptor_set),
            '--input=' + os.path.abspath(intermediate_package_dir),
            '--output=' + os.path.abspath(pkg_dir),
            '--dependencies_config=' + os.path.abspath(
                package_dependencies_yaml),
            '--defaults_config=' + os.path.abspath(package_defaults_yaml),
            '--language=' + language,
            '--short_name=' + api_name,
            '--googleapis_path=' + googleapis_path,
            '--version=' + api_version
        ] + service_args
        self.exec_command(task_utils.gradle_task(
            toolkit_path, 'runGrpcMetadataGen', args))
        return pkg_dir

    # Separated so that this can be mocked for testing
    # TODO (geigerj): remove this and switch to PackageMetadataConfig
    def _googleapis_dir(self, repo_root):
        return os.path.join(repo_root, 'googleapis')
