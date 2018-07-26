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
import glob
from ruamel import yaml

from artman.tasks import task_base
from artman.utils import task_utils


class GapicConfigGenTask(task_base.TaskBase):
    """Generates GAPIC config file"""
    default_provides = 'gapic_config_path'

    def execute(self, toolkit_path, descriptor_set, service_yaml,
                output_dir, api_name, api_version, organization_name):
        api_full_name = task_utils.api_full_name(
            api_name, api_version, organization_name)
        config_gen_dir = os.path.join(
            output_dir, api_full_name + '-config-gen')
        self.exec_command(['mkdir', '-p', config_gen_dir])
        config_gen_path = os.path.join(config_gen_dir,
                                       api_full_name + '_gapic.yaml')
        args = [
            '--descriptor_set=' + os.path.abspath(descriptor_set),
            '--output=' + os.path.abspath(config_gen_path)
        ]
        if service_yaml:
            args = args + ['--service_yaml=' + os.path.abspath(service_yaml)]
        self.exec_command(
            task_utils.gapic_gen_task(toolkit_path, ['GAPIC_CONFIG'] + args))

        return config_gen_path


class DiscoGapicConfigGenTask(task_base.TaskBase):
    """Generates GAPIC config file from a Discovery document"""
    default_provides = 'gapic_config_path'

    def execute(self, toolkit_path, discovery_doc,
        output_dir, api_name, api_version, organization_name):
        api_full_name = task_utils.api_full_name(
            api_name, api_version, organization_name)
        config_gen_dir = os.path.join(
            output_dir, api_full_name + '-config-gen')
        self.exec_command(['mkdir', '-p', config_gen_dir])
        config_gen_path = os.path.join(config_gen_dir,
                                       api_full_name + '_gapic.yaml')
        args = [
            '--discovery_doc=' + os.path.abspath(
                os.path.expanduser(discovery_doc)),
            '--output=' + os.path.abspath(config_gen_path)
        ]
        self.exec_command(
            task_utils.gapic_gen_task(toolkit_path, ['DISCOGAPIC_CONFIG'] + args))

        return config_gen_path


class GapicConfigMoveTask(task_base.TaskBase):
    """Move config file to gapic_yaml location"""

    def _move_to(self, gapic_config_path, gapic_yaml):
        if not gapic_yaml:
            raise ValueError('Could not move generated config file ' \
                'from "{0}" to destination": No location specified'.format(
                os.path.abspath(gapic_config_path)))
        conf_out = os.path.abspath(gapic_yaml)
        if os.path.exists(conf_out):
            # TODO (issue #80): no need to test in remote environment
            olderVersion = conf_out + '.old'
            print('File already exists, save the old version as ' + olderVersion)
            self.exec_command(['mv', conf_out, olderVersion])
        return conf_out

    def execute(self, gapic_config_path, gapic_yaml):
        conf_out = self._move_to(gapic_config_path, gapic_yaml)
        self.exec_command(['mkdir', '-p', os.path.dirname(conf_out)])
        self.exec_command(['cp', gapic_config_path, conf_out])
        return

    def validate(self):
        return []


class GapicCodeGenTask(task_base.TaskBase):
    """Generates GAPIC wrappers"""
    default_provides = 'gapic_code_dir'

    def execute(self, language, toolkit_path, descriptor_set, service_yaml,
                gapic_yaml, package_metadata_yaml,
                gapic_code_dir, api_name, api_version, organization_name,
                aspect):
        existing = glob.glob('%s/*' % gapic_code_dir)
        if existing:
            self.exec_command(['rm', '-r'] + existing)
        gapic_args = ['--gapic_yaml=' + os.path.abspath(gapic_yaml)]
        args = [
            '--descriptor_set=' + os.path.abspath(descriptor_set),
            '--package_yaml2=' + os.path.abspath(package_metadata_yaml),
            '--output=' + os.path.abspath(gapic_code_dir),
            '--language=' + language,
        ]
        if service_yaml:
            args = args + ['--service_yaml=' + os.path.abspath(service_yaml)]
        args = args + gapic_args

        gapic_artifact = ''
        if aspect == 'ALL':
            gapic_artifact = 'LEGACY_GAPIC_AND_PACKAGE'
        elif aspect == 'CODE':
            gapic_artifact = 'GAPIC_CODE'
        elif aspect == 'PACKAGE':
            gapic_artifact = 'GAPIC_PACKAGE'
        else:
            raise ValueError('GapicCodeGenTask: no generation turned on')

        self.exec_command(
            task_utils.gapic_gen_task(toolkit_path, [gapic_artifact] + args))

        return gapic_code_dir


class DiscoGapicCodeGenTask(task_base.TaskBase):
    """Generates GAPIC wrappers from a Discovery document"""
    default_provides = 'gapic_code_dir'

    def execute(self, language, toolkit_path, discovery_doc,
        gapic_yaml, package_metadata_yaml,
        gapic_code_dir, api_name, api_version, organization_name, root_dir):
        existing = glob.glob('%s/*' % gapic_code_dir)
        if existing:
            self.exec_command(['rm', '-r'] + existing)
        gapic_args = ['--gapic_yaml=' + os.path.abspath(gapic_yaml)]
        args = [
                   '--discovery_doc=' + os.path.join(root_dir, discovery_doc),
                   '--package_yaml2=' + os.path.abspath(package_metadata_yaml),
                   '--output=' + os.path.abspath(gapic_code_dir),
                   '--language=' + language,
                   ] + gapic_args

        self.exec_command(
            task_utils.gapic_gen_task(toolkit_path, ['LEGACY_DISCOGAPIC_AND_PACKAGE'] + args))

        return gapic_code_dir


class CSharpGapicPackagingTask(task_base.TaskBase):
    def execute(self, gapic_code_dir, grpc_code_dir, proto_code_dir, gapic_yaml):
        with open(gapic_yaml) as f:
            gapic_config = yaml.load(f, Loader=yaml.Loader)
        package_name = gapic_config.get('language_settings').get('csharp').get('package_name')
        package_root = '{0}/{1}'.format(gapic_code_dir, package_name)
        prod_dir = '{0}/{1}'.format(package_root, package_name)
        # Copy proto/grpc .cs files into prod directory
        self.exec_command(['sh', '-c', 'cp {0}/*.cs {1}'.format(proto_code_dir, prod_dir)])
        self.exec_command(['sh', '-c', 'cp {0}/*.cs {1}'.format(grpc_code_dir, prod_dir)])
