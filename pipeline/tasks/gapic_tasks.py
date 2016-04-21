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
import subprocess
import yaml

from pipeline.tasks import task_base
from pipeline.tasks.requirements import vgen_requirements
from pipeline.utils import lang_params


class GapicConfigGenTask(task_base.TaskBase):
    """Generates GAPIC config file"""
    default_provides = 'intermediate_config_location'

    def execute(self, toolkit_path, descriptor_set, output_dir, api_name):
        config_gen_dir = os.path.join(output_dir, api_name + '-config-gen')
        subprocess.check_call(['mkdir', '-p', config_gen_dir])
        config_gen_path = os.path.join(config_gen_dir,
                                       api_name + '_gapic.yaml')
        args = [
            '--descriptor_set=' + os.path.abspath(descriptor_set),
            '--output=' + os.path.abspath(config_gen_path)
            ]
        clargs = '-Pclargs=' + ','.join(args)
        subprocess.check_call([os.path.join(toolkit_path, 'gradlew'),
                               '-p', toolkit_path, 'runConfigGen', clargs])

        return config_gen_path

    def validate(self):
        return [vgen_requirements.ConfigGenRequirements]


class GapicConfigMoveTask(task_base.TaskBase):
    """Move config file to gapic_api_yaml location"""

    def _move_to(self, intermediate_config_location, gapic_api_yaml):
        error_fmt = 'Could not move generated config file \
                    from "{0}" to "{1}": '.format(
                        os.path.abspath(intermediate_config_location),
                        [os.path.abspath(c_out) for c_out in gapic_api_yaml])

        if len(gapic_api_yaml) > 1:
            raise ValueError(error_fmt + 'Multiple locations specified')
        elif len(gapic_api_yaml) == 0:
            raise ValueError(error_fmt + 'No location specified')
        elif os.path.exists(gapic_api_yaml[0]):
            raise ValueError(error_fmt + 'File already exists')
        else:
            return gapic_api_yaml[0]

    def execute(self, intermediate_config_location, gapic_api_yaml):
        conf_out = self._move_to(intermediate_config_location, gapic_api_yaml)
        if conf_out:
            subprocess.check_call(['mkdir', '-p', os.path.dirname(conf_out)])
            subprocess.check_call(['mv', intermediate_config_location,
                                   conf_out])
        return

    def validate(self):
        return []


class GapicCodeGenTask(task_base.TaskBase):
    """Generates GAPIC wrappers"""
    default_provides = 'intermediate_code_dir'

    def execute(self, language, toolkit_path, descriptor_set, service_yaml,
                gapic_api_yaml, gapic_language_yaml, output_dir, api_name):
        params = lang_params.LANG_PARAMS_MAP[language]
        code_root = params.code_root(
            os.path.join(output_dir, api_name + '-gapic-gen-' + language))
        subprocess.check_call(['rm', '-rf', code_root])
        gapic_yaml = gapic_api_yaml + gapic_language_yaml
        gapic_args = ['--gapic_yaml=' + os.path.abspath(yaml)
                      for yaml in gapic_yaml]
        service_args = ['--service_yaml=' + os.path.abspath(yaml)
                        for yaml in service_yaml]
        args = [
            '--descriptor_set=' + os.path.abspath(descriptor_set),
            '--output=' + os.path.abspath(code_root)
            ] + service_args + gapic_args
        clargs = '-Pclargs=' + ','.join(args)
        subprocess.check_call([os.path.join(toolkit_path, 'gradlew'),
                               '-p', toolkit_path, 'runVGen', clargs])

        return code_root

    def validate(self):
        return [vgen_requirements.VGenRequirements]


class GapicMergeTask(task_base.TaskBase):
    def execute(self, language, toolkit_path, final_repo_dir,
                intermediate_code_dir, auto_merge, auto_resolve, ignore_base):
        params = lang_params.LANG_PARAMS_MAP[language]
        final_code_root = params.code_root(os.path.abspath(final_repo_dir))
        baseline_root = params.code_root(
            os.path.abspath(os.path.join(final_repo_dir, 'baseline')))
        args = [
            '--source_path=' + final_code_root,
            '--generated_path=' + os.path.abspath(intermediate_code_dir),
            '--baseline_path=' + baseline_root,
            ]
        if auto_merge:
            args.append('--auto_merge')
        if auto_resolve:
            args.append('--auto_resolve')
        if ignore_base:
            args.append('--ignore_base')
        clargs = '-Pclargs=' + ','.join(args)
        print 'Running synchronizer with args: ' + str(args)
        subprocess.check_call([os.path.join(toolkit_path, 'gradlew'),
                               '-p', toolkit_path, 'runSynchronizer',
                               clargs])
        for root, subdirs, files in os.walk(final_code_root):
            for file in files:
                if file.endswith('.orig'):
                    os.remove(os.path.join(root, file))

    def validate(self):
        return [vgen_requirements.MergeRequirements]


class GoExtractImportBaseTask(task_base.TaskBase):
    default_provides = 'go_import_base'

    def execute(self, gapic_api_yaml):
        for yaml_file in gapic_api_yaml:
            if not os.path.exists(yaml_file):
                continue
            with open(yaml_file) as f:
                gapic_config = yaml.load(f)
            if not gapic_config:
                continue
            language_settings = gapic_config.get('language_settings')
            if not language_settings:
                continue
            go_settings = language_settings.get('go')
            if not go_settings:
                continue
            if 'package_name' in go_settings:
                return go_settings.get('package_name')
