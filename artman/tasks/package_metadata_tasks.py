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

from ruamel import yaml

from artman.tasks import task_base
from artman.utils import task_utils

# Metadata config gen

class PackageMetadataConfigGenTask(task_base.TaskBase):
    """Generates package metadata config"""
    default_provides = 'package_metadata_yaml'

    def execute(self, api_name, api_version, organization_name, output_dir,
                package_dependencies_yaml, package_defaults_yaml, proto_deps,
                language, local_paths, src_proto_path, package_type,
                gapic_api_yaml, release_level=None, packaging='single-artifact',
                generated_package_version=None, proto_test_deps=None):
        api_full_name = task_utils.api_full_name(
            api_name, api_version, organization_name)

        config = self._create_config(
            api_name, api_version, api_full_name, output_dir,
            package_dependencies_yaml, package_defaults_yaml, proto_deps,
            proto_test_deps, language, local_paths, src_proto_path, package_type,
            gapic_api_yaml, release_level=release_level, packaging=packaging,
            generated_package_version=generated_package_version)

        package_metadata_config = os.path.join(
            output_dir, api_full_name + '_package.yaml')
        self._write_yaml(config, package_metadata_config)

        return package_metadata_config

    def _create_config(self, api_name, api_version, api_full_name, output_dir,
                       package_dependencies_yaml, package_defaults_yaml, proto_deps,
                       proto_test_deps, language, local_paths, src_proto_path, package_type,
                       gapic_api_yaml, release_level=None,packaging='single-artifact',
                       generated_package_version=None):
        googleapis_dir = local_paths['googleapis']
        googleapis_path = os.path.commonprefix(
            [os.path.relpath(p, googleapis_dir) for p in src_proto_path])

        with open(package_dependencies_yaml) as dep_file:
            package_dependencies = yaml.load(dep_file, Loader=yaml.Loader)
        with open(package_defaults_yaml) as dep_file:
            package_defaults = yaml.load(dep_file, Loader=yaml.Loader)

        # Apply package version and development status overrides if specified
        # in the artman config
        if generated_package_version is not None:
            package_defaults['generated_package_version'][language] = (
                generated_package_version)
        if release_level is not None:
            package_defaults['release_level'][language] = (
                release_level)

        gapic_config_name = ''
        if len(gapic_api_yaml) > 0:
            gapic_config_name = os.path.basename(gapic_api_yaml[0])

        dependency_type = 'local'
        if packaging == 'single-artifact':
            dependency_type = 'release'

        config = {
            'short_name': api_name,
            'major_version': api_version,
            'proto_path': googleapis_path,
            'package_name': {
                'default': api_full_name,
            },
            'proto_deps': proto_deps,
            'package_type': package_type,
            'dependency_type': dependency_type,
            'gapic_config_name': gapic_config_name,
        }

        if proto_test_deps:
            config['proto_test_deps'] = proto_test_deps

        config.update(package_dependencies)
        config.update(package_defaults)

        return config

    # Separated so that this can be mocked for testing
    def _write_yaml(self, config_dict, dest):
        with open(dest, 'w') as f:
            yaml.safe_dump(config_dict, f, default_flow_style=False)

class JavaGrpcPackageMetadataConfigGenTask(PackageMetadataConfigGenTask):
    def _create_config(self, api_name, api_version, api_full_name, output_dir,
                package_dependencies_yaml, package_defaults_yaml, proto_deps,
                proto_test_deps, language, local_paths, src_proto_path, package_type,
                gapic_api_yaml, release_level=None, packaging='single-artifact',
                generated_package_version=None):
        config = super(JavaGrpcPackageMetadataConfigGenTask, self)._create_config(
            api_name, api_version, api_full_name, output_dir,
            package_dependencies_yaml, package_defaults_yaml, proto_deps,
            proto_test_deps, language, local_paths, src_proto_path, package_type,
            gapic_api_yaml, release_level=release_level, packaging=packaging,
            generated_package_version=generated_package_version)
        config['generation_layer'] = 'grpc'

        return config

class JavaProtoPackageMetadataConfigGenTask(PackageMetadataConfigGenTask):
    def _create_config(self, api_name, api_version, api_full_name, output_dir,
                package_dependencies_yaml, package_defaults_yaml, proto_deps,
                proto_test_deps, language, local_paths, src_proto_path, package_type,
                gapic_api_yaml, release_level=None, packaging='single-artifact',
                generated_package_version=None):
        config = super(JavaProtoPackageMetadataConfigGenTask, self)._create_config(
            api_name, api_version, api_full_name, output_dir,
            package_dependencies_yaml, package_defaults_yaml, proto_deps,
            proto_test_deps, language, local_paths, src_proto_path, package_type,
            gapic_api_yaml, release_level=release_level, packaging=packaging,
            generated_package_version=generated_package_version)
        config['generation_layer'] = 'proto'

        return config

# Metadata gen

class ProtoPackageMetadataGenTaskBase(task_base.TaskBase):
    def _execute(self, api_name, api_version, organization_name, local_paths,
                descriptor_set, src_proto_path, service_yaml,
                input_dir, output_dir, package_metadata_yaml,
                language):
        toolkit_path = local_paths['toolkit']
        api_full_name = task_utils.api_full_name(
            api_name, api_version, organization_name)
        proto_prefix = self._get_proto_prefix()
        pkg_dir = os.path.join(
            output_dir, language, proto_prefix + api_full_name)

        service_args = ['--service_yaml=' + os.path.abspath(yaml)
                        for yaml in service_yaml]
        args = [
            '--descriptor_set=' + os.path.abspath(descriptor_set),
            '--input=' + os.path.abspath(input_dir),
            '--output=' + os.path.abspath(pkg_dir),
            '--metadata_config=' + os.path.abspath(package_metadata_yaml),
            '--language=' + language,
        ] + service_args
        self.exec_command(task_utils.gradle_task(
            toolkit_path, 'runGrpcMetadataGen', args))

        return pkg_dir

    # Separated so that this can be overriden by each language subclass
    def _get_proto_prefix(self):
        return 'proto-'

class ProtoPackageMetadataGenTask(ProtoPackageMetadataGenTaskBase):
    default_provides = 'proto_pkg_dir'

    def execute(self, api_name, api_version, organization_name, local_paths,
                descriptor_set, src_proto_path, service_yaml,
                proto_code_dir, output_dir, package_metadata_yaml,
                language):
        return self._execute(api_name, api_version, organization_name,
                local_paths, descriptor_set, src_proto_path, service_yaml,
                proto_code_dir, output_dir, package_metadata_yaml,
                language)

class GrpcPackageMetadataGenTask(ProtoPackageMetadataGenTaskBase):
    default_provides = 'grpc_pkg_dir'

    def execute(self, api_name, api_version, organization_name, local_paths,
                descriptor_set, src_proto_path, service_yaml,
                grpc_code_dir, output_dir, package_metadata_yaml,
                language):
        return self._execute(api_name, api_version, organization_name,
                local_paths, descriptor_set, src_proto_path, service_yaml,
                grpc_code_dir, output_dir, package_metadata_yaml,
                language)

    def _get_proto_prefix(self):
        return 'grpc-'
