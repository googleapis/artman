"""Tasks that perform cleanup after code generation"""

import os
import subprocess
from taskflow import task


class CleanUpTask(task.Task):
  """Recursively removes all entries in `output_dir` that are not included in
  `saved_dirs`"""
  def execute(self, output_dir, saved_dirs):
    print 'Cleaning up temporary files'
    for entry in os.listdir(output_dir):
        if not entry in saved_dirs:
            subprocess.call(['rm', '-rf', os.path.join(output_dir, entry)])
