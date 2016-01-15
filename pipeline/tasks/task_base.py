"""Base class for pipeline task.

This base class extends taskflow Task class, with additional methods and
properties used by veneer pipeline."""

from taskflow.task import Task


class TaskBase(Task):

  @staticmethod
  def requires():
    """Abstract method, which returns list of task requirements.

    Subclass must implment this method, and return list of task requirements
    classes.
    """
    raise NotImplementedError("Subclass must implement abstract method")
