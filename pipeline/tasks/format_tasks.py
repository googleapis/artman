"""Tasks related to format"""

import os
import subprocess
from pipeline.tasks import task_base
from pipeline.tasks.requirements import format_requirements


# TODO: Store both intermediate and final output in all format tasks.

class JavaFormatTask(task_base.TaskBase):
    def execute(self, output_dir):
        print 'Formatting files in ' + os.path.abspath(output_dir)
        # TODO(shinfan): figure out how to get this distributed and made
        # available to the pipeline instead of having to do a download.
        path = os.path.join(format_requirements.JavaFormatRequirement.DIR,
                            format_requirements.JavaFormatRequirement.FILENAME)
        targetFiles = []
        for root, dirs, files in os.walk(output_dir):
            for filename in files:
                if filename.endswith('.java'):
                    targetFile = os.path.abspath(os.path.join(root, filename))
                    targetFiles.append(targetFile)
        subprocess.call(
            ['java', '-jar', path, '--replace'] + targetFiles)

    def validate(self):
        return [format_requirements.JavaFormatRequirement]


class PythonFormatTask(task_base.TaskBase):
    def execute(self, output_dir):
        print 'Formatting files in ' + os.path.abspath(output_dir)
        targetFiles = []
        for root, dirs, files in os.walk(output_dir):
            for filename in files:
                # TODO(jgeiger): change to `endswith('.py')` once the packman
                # task is functioning. Currently, it takes too long to run the
                # formatter on the gRPC codegen output.
                if filename.endswith('api.py'):
                    targetFile = os.path.abspath(os.path.join(root, filename))
                    targetFiles.append(targetFile)

        subprocess.call(['yapf', '-i'] + targetFiles)

    # yapf is installed by tox for the entire pipeline project's virtualenv,
    # so we shouldn't need a separate validation task.
    def validate(self):
        return []
