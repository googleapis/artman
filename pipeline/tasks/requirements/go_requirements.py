"""Requirements classes related to Go."""

import os

from task_requirement_base import TaskRequirementBase


class GoPathRequirements(TaskRequirementBase):

    @classmethod
    def install(cls):
        # Intentionally do nothing.
        pass

    @classmethod
    def require(cls):
        # Intentionally do nothing.
        return []

    @classmethod
    def is_installed(cls):
        return 'GOPATH' in os.environ


class GoFormatRequirements(TaskRequirementBase):

    @classmethod
    def install(cls):
        pass

    @classmethod
    def require(cls):
        return ['gofmt']
