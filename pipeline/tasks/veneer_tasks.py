"""Tasks related to generation of Veneer wrappers"""

import os
import subprocess
from taskflow import task
from pipeline.tasks.requirements import vgen_requirements


class VeneerCodeGenTask(task.Task):
    """Generates Veneer wrappers"""
    def execute(self, gapi_tools_path, descriptor_set, service_yaml,
                veneer_yaml, output_dir):
        veneer_args = ['--veneer_yaml=' + os.path.abspath(yaml)
                       for yaml in veneer_yaml]
        service_args = ['--service_yaml=' + os.path.abspath(yaml)
                        for yaml in service_yaml]
        args = [
            '--descriptor_set=' + os.path.abspath(descriptor_set),
            '--output=' + os.path.abspath(output_dir)
            ] + service_args + veneer_args
        clargs = '-Pclargs=' + ','.join(args)
        subprocess.call([os.path.join(gapi_tools_path, 'gradlew'),
                         '-p', gapi_tools_path, 'runVGen', clargs])

    def validate(self):
        return [vgen_requirements.VGenRequirements]
