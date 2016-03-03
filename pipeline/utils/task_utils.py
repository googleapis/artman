"""Utility functions related to tasks"""

import subprocess


def runGradleTask(task_name, task_path):
    output = subprocess.check_output(
        ['./gradlew', task_name], cwd=task_path)
    # It is a convention that gradle task uses 'output: ' as
    # prefix in their output
    prefix = 'output: '
    for line in output.split('\n'):
        if line.startswith(prefix):
            return line[len(prefix):]
    return None
