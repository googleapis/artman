"""Tasks related to generation of Veneer wrappers"""

import os
import subprocess
from taskflow import task
from pipeline.tasks.requirements import vgen_requirements
from pipeline.utils import lang_params


class VeneerCodeGenTask(task.Task):
    """Generates Veneer wrappers"""
    default_provides = 'intermediate_code_dir'

    def execute(self, language, gapi_tools_path, descriptor_set, service_yaml,
                veneer_yaml, output_dir, api_name):
        params = lang_params.LANG_PARAMS_MAP[language]
        code_root = params.code_root(
            os.path.join(output_dir, api_name + '-veneer-gen-' + language))
        veneer_args = ['--veneer_yaml=' + os.path.abspath(yaml)
                       for yaml in veneer_yaml]
        service_args = ['--service_yaml=' + os.path.abspath(yaml)
                        for yaml in service_yaml]
        args = [
            '--descriptor_set=' + os.path.abspath(descriptor_set),
            '--output=' + os.path.abspath(code_root)
            ] + service_args + veneer_args
        clargs = '-Pclargs=' + ','.join(args)
        subprocess.call([os.path.join(gapi_tools_path, 'gradlew'),
                         '-p', gapi_tools_path, 'runVGen', clargs])

        return code_root

    def validate(self):
        return [vgen_requirements.VGenRequirements]


class VeneerMergeTask(task.Task):
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
            args += '--auto_merge'
        if auto_resolve:
            args += '--auto_resolve'
        if ignore_base:
            args += '--ignore_base'
        clargs = '-Pclargs=' + ','.join(args)
        subprocess.call([os.path.join(gapi_tools_path, 'gradlew'),
                         '-p', gapi_tools_path, 'runSynchronizer', clargs])

    def validate(self):
        return [vgen_requirements.MergeRequirements]
