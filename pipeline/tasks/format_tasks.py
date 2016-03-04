"""Tasks related to format"""

import os
import subprocess
from pipeline.tasks import task_base
from pipeline.tasks.requirements import go_requirements
from pipeline.utils import task_utils


# TODO: Store both intermediate and final output in all format tasks.

class JavaFormatTask(task_base.TaskBase):
    def execute(self, intermediate_code_dir, gapi_tools_path):
        print 'Formatting files in ' + os.path.abspath(intermediate_code_dir)
        # TODO(shinfan): Move gradle task into requirement
        path = task_utils.runGradleTask(
                'showJavaFormatterPath', gapi_tools_path)
        targetFiles = []
        for root, dirs, files in os.walk(intermediate_code_dir):
            for filename in files:
                if filename.endswith('.java'):
                    targetFile = os.path.abspath(os.path.join(root, filename))
                    targetFiles.append(targetFile)
        subprocess.check_call(
            ['java', '-jar', path, '--replace'] + targetFiles)

    def validate(self):
        return []


class PythonFormatTask(task_base.TaskBase):
    def execute(self, intermediate_code_dir):
        print 'Formatting files in ' + os.path.abspath(intermediate_code_dir)
        targetFiles = []
        for root, dirs, files in os.walk(intermediate_code_dir):
            for filename in files:
                # TODO(jgeiger): change to `endswith('.py')` once the packman
                # task is functioning. Currently, it takes too long to run the
                # formatter on the gRPC codegen output.
                if filename.endswith('api.py'):
                    targetFile = os.path.abspath(os.path.join(root, filename))
                    targetFiles.append(targetFile)
        subprocess.check_call(['yapf', '-i'] + targetFiles)

    # yapf is installed by tox for the entire pipeline project's virtualenv,
    # so we shouldn't need a separate validation task.
    def validate(self):
        return []


class GoFormatTask(task_base.TaskBase):
    def execute(self, intermediate_code_dir):
        print 'Formatting files in ' + os.path.abspath(intermediate_code_dir)
        subprocess.check_call(['gofmt', '-w', intermediate_code_dir])

    def validate(self):
        return [go_requirements.GoFormatRequirements]
