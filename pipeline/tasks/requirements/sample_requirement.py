"""A canonical example of a task requirement class."""

import subprocess

from task_requirement_base import TaskRequirementBase


class SampleRequirement(TaskRequirementBase):

  @classmethod
  def install(cls):
    """ Just do ls."""
    subprocess.call(["ls", "-l"])

  @classmethod
  def require(cls):
    return ["ls"]
