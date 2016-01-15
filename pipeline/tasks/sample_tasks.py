"""Canonical examples on create tasks."""

import os
import subprocess
import sys
import time

from task_base import TaskBase
from requirements.sample_requirement import SampleRequirement


class SampleTask(TaskBase):
  """A sample task"""

  def execute(self, sleep_secs):
    print('Sleep %d sec.' % sleep_secs)
    time.sleep(sleep_secs)

  @staticmethod
  def requires():
    return [SampleRequirement]
