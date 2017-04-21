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

_PROTO_PREFIX_MAP = {
    'java': 'grpc-',
    'python': 'proto-'
}


class PackageMetadataConfigGenTask(task_base.TaskBase):
    """Generates package metadata config"""
    default_provides = 'package_metadata_yaml'

    def execute(self, api_name, api_version, organization_name, output_dir,
                package_dependencies_yaml, package_defaults_yaml, proto_deps,
                local_paths, src_proto_path, package_type, gapic_api_yaml,
                generation_layer=None):
        googleapis_dir = local_paths['googleapis']
        googleapis_path = os.path.commonprefix(
            [os.path.relpath(p, googleapis_dir) for p in src_proto_path])
        api_full_name = task_utils.api_full_name(
            api_name, api_version, organization_name)

        with open(package_dependencies_yaml) as dep_file:
            package_dependencies = yaml.load(dep_file, Loader=yaml.Loader)
        with open(package_defaults_yaml) as dep_file:
            package_defaults = yaml.load(dep_file, Loader=yaml.Loader)

        gapic_config_name = ''
        if len(gapic_api_yaml) > 0:
            gapic_config_name = os.path.basename(gapic_api_yaml[0])

        config = {
            'short_name': api_name,
            'major_version': api_version,
            'proto_path': googleapis_path,
            'package_name': {
                'default': api_full_name,
            },
            'proto_deps': proto_deps,
            'package_type': package_type,
            'gapic_config_name': gapic_config_name,
            'generation_layer': generation_layer
        }

        config.update(package_dependencies)
        config.update(package_defaults)

        package_metadata_config = os.path.join(
            output_dir, api_full_name + '_package.yaml')
        self._write_yaml(config, package_metadata_config)

        return package_metadata_config

    # Separated so that this can be mocked for testing
    def _write_yaml(self, config_dict, dest):
        with open(dest, 'w') as f:
            yaml.safe_dump(config_dict, f, default_flow_style=False)


class JavaGrpcPackageTypeTask(task_base.TaskBase):
    default_provides = 'generation_layer'

    def execute(self):
        return 'grpc'

class JavaProtoPackageTypeTask(task_base.TaskBase):
    default_provides = 'generation_layer'

    def execute(self):
        return 'proto'


class ProtoPackageMetadataGenTask(task_base.TaskBase):
    default_provides = 'grpc_code_dir'

    def execute(self, api_name, api_version, organization_name, local_paths,
                descriptor_set, src_proto_path, service_yaml,
                grpc_code_dir, output_dir, package_metadata_yaml,
                language, generation_layer=None):
        toolkit_path = local_paths['toolkit']
        api_full_name = task_utils.api_full_name(
            api_name, api_version, organization_name)
        if generation_layer:
            proto_prefix = generation_layer + '-'
        else:
            proto_prefix = _PROTO_PREFIX_MAP[language]
        pkg_dir = os.path.join(
            output_dir, language, proto_prefix + api_full_name)

        service_args = ['--service_yaml=' + os.path.abspath(yaml)
                        for yaml in service_yaml]
        args = [
            '--descriptor_set=' + os.path.abspath(descriptor_set),
            '--input=' + os.path.abspath(grpc_code_dir),
            '--output=' + os.path.abspath(pkg_dir),
            '--metadata_config=' + os.path.abspath(package_metadata_yaml),
            '--language=' + language,
        ] + service_args
        self.exec_command(task_utils.gradle_task(
            toolkit_path, 'runGrpcMetadataGen', args))
        self.exec_command(['rm', '-rf', grpc_code_dir])

        # This becomes the new `grpc_code_dir` for subsequent tasks.
        return pkg_dir
