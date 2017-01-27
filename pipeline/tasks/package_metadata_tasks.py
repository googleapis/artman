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
            'package_name': {
                'default': api_full_name
            }
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


class ProtoPackageMetadataGenTask(task_base.TaskBase):
    default_provides = 'package_dir'

    def execute(self, api_name, api_version, organization_name, toolkit_path,
                descriptor_set, src_proto_path, service_yaml,
                intermediate_package_dir, output_dir, package_metadata_yaml,
                language):
        api_full_name = task_utils.api_full_name(
            api_name, api_version, organization_name)
        pkg_dir = os.path.join(output_dir, 'python', 'proto-' + api_full_name)

        service_args = ['--service_yaml=' + os.path.abspath(yaml)
                        for yaml in service_yaml]
        args = [
            '--descriptor_set=' + os.path.abspath(descriptor_set),
            '--input=' + os.path.abspath(intermediate_package_dir),
            '--output=' + os.path.abspath(pkg_dir),
            '--metadata_config=' + os.path.abspath(package_metadata_yaml),
            '--language=' + language,
        ] + service_args
        self.exec_command(task_utils.gradle_task(
            toolkit_path, 'runGrpcMetadataGen', args))
        return pkg_dir
