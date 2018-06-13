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

import io
import os

from ruamel import yaml

from artman.tasks import task_base
from artman.utils import task_utils

# Metadata config gen

class PackageMetadataConfigGenTask(task_base.TaskBase):
    """Generates package metadata config"""
    default_provides = 'package_metadata_yaml'

    def execute(self, api_name, api_version, organization_name, output_dir,
                proto_deps, language, root_dir, src_proto_path,
                gapic_api_yaml, artifact_type, release_level=None,
                proto_test_deps=None):
        api_full_name = task_utils.api_full_name(
            api_name, api_version, organization_name)

        config = self._create_config(
            api_name, api_version, organization_name, output_dir, proto_deps,
            proto_test_deps, language, root_dir, src_proto_path,
            gapic_api_yaml, artifact_type, release_level)

        package_metadata_config = os.path.join(
            output_dir, language + '_' + api_full_name + '_package2.yaml')
        self._write_yaml(config, package_metadata_config)

        return package_metadata_config

    def _create_config(self, api_name, api_version, organization_name, output_dir,
                       proto_deps, proto_test_deps, language, root_dir, src_proto_path,
                       gapic_api_yaml, artifact_type, release_level):
        googleapis_dir = root_dir
        googleapis_path = os.path.commonprefix(
            [os.path.relpath(p, googleapis_dir) for p in src_proto_path])

        config = {
            'api_name': api_name,
            'api_version': api_version,
            'organization_name': organization_name,
            'proto_deps': proto_deps,
            'release_level': release_level,
            'artifact_type': artifact_type,
            'proto_path': googleapis_path,
        }

        if proto_test_deps:
            config['proto_test_deps'] = proto_test_deps

        return config

    # Separated so that this can be mocked for testing
    def _write_yaml(self, config_dict, dest):
        with io.open(dest, 'w', encoding='UTF-8') as f:
            yaml.safe_dump(config_dict, f, default_flow_style=False)

# Metadata gen

class ProtoPackageMetadataGenTaskBase(task_base.TaskBase):
    def _execute(self, api_name, api_version, organization_name, toolkit,
                descriptor_set, src_proto_path, service_yaml,
                input_dir, output_dir, package_metadata_yaml,
                language, artifact_type):
        toolkit_path = toolkit
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
            '--package_yaml2=' + os.path.abspath(package_metadata_yaml),
            '--artifact_type=' + artifact_type,
            '--language=' + language,
        ] + service_args
        self.exec_command(
            task_utils.gapic_gen_task(toolkit_path, ['LEGACY_GRPC_PACKAGE'] + args))

        return pkg_dir

    # Separated so that this can be overriden by each language subclass
    def _get_proto_prefix(self):
        return 'proto-'

class ProtoPackageMetadataGenTask(ProtoPackageMetadataGenTaskBase):
    default_provides = 'proto_pkg_dir'

    def execute(self, api_name, api_version, organization_name, toolkit,
                descriptor_set, src_proto_path, service_yaml,
                proto_code_dir, output_dir, package_metadata_yaml,
                language):
        return self._execute(api_name, api_version, organization_name,
                toolkit, descriptor_set, src_proto_path, service_yaml,
                proto_code_dir, output_dir, package_metadata_yaml,
                language, 'PROTOBUF')

class GrpcPackageMetadataGenTask(ProtoPackageMetadataGenTaskBase):
    default_provides = 'grpc_pkg_dir'

    def execute(self, api_name, api_version, organization_name, toolkit,
                descriptor_set, src_proto_path, service_yaml,
                grpc_code_dir, output_dir, package_metadata_yaml,
                language):
        return self._execute(api_name, api_version, organization_name,
                toolkit, descriptor_set, src_proto_path, service_yaml,
                grpc_code_dir, output_dir, package_metadata_yaml,
                language, 'GRPC')

    def _get_proto_prefix(self):
        return 'grpc-'
