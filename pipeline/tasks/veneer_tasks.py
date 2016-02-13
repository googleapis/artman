"""Tasks related to generation of Veneer wrappers"""

import os
import subprocess
from taskflow import task
from pipeline.tasks.requirements import vgen_requirements
from pipeline.utils import lang_params


class VeneerCodeGenTask(task.Task):
    """Generates Veneer wrappers"""
    default_provides = 'code_dir'

    def execute(self, language, gapi_tools_path, descriptor_set, service_yaml,
                veneer_yaml, vgen_output_dir):
        params = lang_params.LANG_PARAMS_MAP[language]
        code_root = params.code_root(vgen_output_dir)
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
