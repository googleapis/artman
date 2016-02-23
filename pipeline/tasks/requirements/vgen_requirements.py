"""Requirements to run VGen"""

from pipeline.tasks.requirements import task_requirement_base


class VGenRequirements(task_requirement_base.TaskRequirementBase):

    @classmethod
    def require(cls):
        return ['java']

    @classmethod
    def install(cls):
        # TODO(jgeiger): Do we really want to auto-install Java?
        raise Exception('Java not installed')


class MergeRequirements(task_requirement_base.TaskRequirementBase):

    @classmethod
    def require(cls):
        return ['kdiff3']

    @classmethod
    def install(cls):
        # TODO(shinfan): Install kdiff3
        raise Exception('Kdiff3 not installed')