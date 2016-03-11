"""Tasks related to generation of Veneer wrappers"""

import os
import subprocess
import yaml

from pipeline.tasks import task_base
from pipeline.tasks.requirements import vgen_requirements
from pipeline.utils import lang_params


class VeneerCodeGenTask(task_base.TaskBase):
    """Generates Veneer wrappers"""
    default_provides = 'intermediate_code_dir'

    def execute(self, language, gapi_tools_path, descriptor_set, service_yaml,
                veneer_api_yaml, veneer_language_yaml, output_dir, api_name):
        params = lang_params.LANG_PARAMS_MAP[language]
        code_root = params.code_root(
            os.path.join(output_dir, api_name + '-veneer-gen-' + language))
        veneer_yaml = veneer_api_yaml + veneer_language_yaml
        veneer_args = ['--veneer_yaml=' + os.path.abspath(yaml)
                       for yaml in veneer_yaml]
        service_args = ['--service_yaml=' + os.path.abspath(yaml)
                        for yaml in service_yaml]
        args = [
            '--descriptor_set=' + os.path.abspath(descriptor_set),
            '--output=' + os.path.abspath(code_root)
            ] + service_args + veneer_args
        clargs = '-Pclargs=' + ','.join(args)
        subprocess.check_call([os.path.join(gapi_tools_path, 'gradlew'),
                               '-p', gapi_tools_path, 'runVGen', clargs])

        return code_root

    def validate(self):
        return [vgen_requirements.VGenRequirements]


class VeneerMergeTask(task_base.TaskBase):
    def execute(self, language, gapi_tools_path, final_repo_dir,
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
        subprocess.check_call([os.path.join(gapi_tools_path, 'gradlew'),
                               '-p', gapi_tools_path, 'runSynchronizer',
                               clargs])
        for root, subdirs, files in os.walk(final_code_root):
            for file in files:
                if file.endswith('.orig'):
                    os.remove(os.path.join(root, file))

    def validate(self):
        return [vgen_requirements.MergeRequirements]


class GoExtractImportBaseTask(task_base.TaskBase):
    default_provides = 'go_import_base'

    def execute(self, veneer_api_yaml):
        for yaml_file in veneer_api_yaml:
            if not os.path.exists(yaml_file):
                continue
            with open(yaml_file) as f:
                veneer_config = yaml.load(f)
            if not veneer_config:
                continue
            language_settings = veneer_config.get('language_settings')
            if not language_settings:
                continue
            go_settings = language_settings.get('go')
            if not go_settings:
                continue
            if 'package_name' in go_settings:
                return go_settings.get('package_name')
