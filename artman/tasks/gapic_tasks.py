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
"""Tasks related to generation of GAPIC wrappers"""

import os

from artman.tasks import packman_tasks
from artman.tasks import task_base
from artman.utils import task_utils
from artman.tasks.requirements import gapic_requirements


class GapicConfigGenTask(task_base.TaskBase):
    """Generates GAPIC config file"""
    default_provides = 'gapic_config_dir'

    def execute(self, toolkit_path, descriptor_set, service_yaml,
                output_dir, api_name, api_version, organization_name):
        api_full_name = task_utils.api_full_name(
            api_name, api_version, organization_name)
        config_gen_dir = os.path.join(
            output_dir, api_full_name + '-config-gen')
        self.exec_command(['mkdir', '-p', config_gen_dir])
        config_gen_path = os.path.join(config_gen_dir,
                                       api_full_name + '_gapic.yaml')
        service_args = ['--service_yaml=' + os.path.abspath(yaml)
                        for yaml in service_yaml]
        args = [
            '--descriptor_set=' + os.path.abspath(descriptor_set),
            '--output=' + os.path.abspath(config_gen_path)
        ] + service_args
        self.exec_command(
            task_utils.gradle_task(toolkit_path, 'runConfigGen', args))

        return config_gen_path

    def validate(self):
        return [gapic_requirements.ConfigGenRequirements]


class GapicConfigMoveTask(task_base.TaskBase):
    """Move config file to gapic_api_yaml location"""

    def _move_to(self, gapic_config_dir, gapic_api_yaml):
        error_fmt = 'Could not move generated config file ' \
                    'from "{0}" to "{1}": '.format(
                        os.path.abspath(gapic_config_dir),
                        [os.path.abspath(c_out) for c_out in gapic_api_yaml])

        if len(gapic_api_yaml) > 1:
            raise ValueError(error_fmt + 'Multiple locations specified')
        elif len(gapic_api_yaml) == 0:
            raise ValueError(error_fmt + 'No location specified')
        conf_out = os.path.abspath(gapic_api_yaml[0])
        if os.path.exists(conf_out):
            # TODO (issue #80): no need to test in remote environment
            raise ValueError(error_fmt + 'File already exists')
        else:
            return conf_out

    def execute(self, gapic_config_dir, gapic_api_yaml):
        conf_out = self._move_to(gapic_config_dir, gapic_api_yaml)
        self.exec_command(['mkdir', '-p', os.path.dirname(conf_out)])
        self.exec_command(['mv', gapic_config_dir, conf_out])
        return

    def validate(self):
        return []


class GapicCodeGenTask(task_base.TaskBase):
    """Generates GAPIC wrappers"""
    default_provides = 'gapic_code_dir'

    def execute(self, language, toolkit_path, descriptor_set, service_yaml,
                gapic_api_yaml, gapic_language_yaml, package_metadata_yaml,
                gapic_code_dir, api_name, api_version, organization_name,
                packaging='single-artifact'):
        self.exec_command(['rm', '-rf', '%s/*' % gapic_code_dir])
        gapic_yaml = gapic_api_yaml + gapic_language_yaml
        gapic_args = ['--gapic_yaml=' + os.path.abspath(yaml)
                      for yaml in gapic_yaml]
        service_args = ['--service_yaml=' + os.path.abspath(yaml)
                        for yaml in service_yaml]
        args = [
            '--descriptor_set=' + os.path.abspath(descriptor_set),
            '--package_yaml=' + os.path.abspath(package_metadata_yaml),
            '--output=' + os.path.abspath(gapic_code_dir),
        ] + service_args + gapic_args

        # Enable sample app generator if the packaging is set to single-artifact
        if packaging == 'single-artifact':
            args += ['--enabled_artifacts=surface']
            args += ['--enabled_artifacts=test']
            args += ['--enabled_artifacts=sample_app']

        self.exec_command(
            task_utils.gradle_task(toolkit_path, 'runCodeGen', args))

        return gapic_code_dir

    def validate(self):
        return [gapic_requirements.GapicRequirements]


class JavaGapicPackagingTask(task_base.TaskBase):
    def execute(self, gapic_code_dir, packaging='single-artifact',
                grpc_code_dir=None, proto_code_dir=None):
        if packaging == 'single-artifact':
            if grpc_code_dir:
                self.exec_command(['cp', '-rf', grpc_code_dir, gapic_code_dir])

            if proto_code_dir:
                self.exec_command(['cp', '-rf', proto_code_dir, gapic_code_dir])

            self.exec_command([gapic_code_dir + '/gradlew', '-p', gapic_code_dir, 'jar'])


class GapicPackmanTask(packman_tasks.PackmanTaskBase):
    default_provides = 'package_dir'

    def execute(self, language, api_name, api_version, organization_name,
                gapic_code_dir, skip_packman=False):
        if not skip_packman:
            api_full_name = task_utils.api_full_name(
                api_name, api_version, organization_name)
            # TODO: Use TaskBase.exec_command()
            self.run_packman(language,
                             task_utils.packman_api_name(api_full_name),
                             '--gax_dir=' + gapic_code_dir,
                             '--template_root=templates/gax')
        return gapic_code_dir
