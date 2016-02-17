"""Utility functions related to tasks"""

import subprocess


def runGradleTask(task_name, task_path, keyword):
    output = subprocess.check_output(
        ['./gradlew', task_name], cwd=task_path)
    for line in output.split('\n'):
        if keyword in line:
            return line
    return None
