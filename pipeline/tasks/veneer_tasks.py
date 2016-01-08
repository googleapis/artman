"""Tasks related to generation of Veneer wrappers"""

import os
import subprocess
from taskflow import task
from pipeline.tasks import prerequesites


class JavaCheckTask(task.Task):
    """Checks whether Java is on the system path"""
    def execute(self):
        try:
            with open(os.devnull, 'wb') as devnull:
                subprocess.check_call(['which', 'java'], stdout=devnull)
        except subprocess.CalledProcessError:
            raise prerequesites.PrerequesiteError(
                'java', 'Ensure java is installed.')


class GradleCheckTask(task.Task):
    """Checks whether gradlew and build.gradle are in the gapi_tools_path"""
    def execute(self, gapi_tools_path):
        if not (os.path.isfile(os.path.join(gapi_tools_path, 'gradlew')) and
                os.path.isfile(os.path.join(gapi_tools_path, 'build.gradle'))):
            raise prerequesites.PrerequesiteError(
                'Gradle wrapper or tasks',
                'Not found at specified location: ' +
                gapi_tools_path)


class VeneerCodeGenTask(task.Task):
    """Generates Veneer wrappers"""
    def execute(self, gapi_tools_path, descriptor_set, service_yaml, veneer_yaml,
                output_dir):
        clargs = '-Pclargs=' + ','.join(
            ['--descriptorSet=' + os.path.abspath(descriptor_set),
             '--output=' + os.path.abspath(output_dir)] +
            ['--serviceYaml=' + os.path.abspath(yaml) for yaml in service_yaml] +
            ['--veneerYaml=' + os.path.abspath(yaml) for yaml in veneer_yaml])
        subprocess.call([os.path.join(gapi_tools_path, 'gradlew'),
                         '-p', gapi_tools_path, 'runVGen', clargs])
