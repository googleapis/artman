"""Canonical examples on create tasks."""

import os
import subprocess
import sys
import time

from pipeline.tasks import task_base
from requirements import sample_requirement


class SampleTask(task_base.TaskBase):
  """A sample task"""

  def execute(self, sleep_secs):
    print('Sleep %d sec.' % sleep_secs)
    time.sleep(sleep_secs)

  @staticmethod
  def requires():
    return [sample_requirement.SampleRequirement]
