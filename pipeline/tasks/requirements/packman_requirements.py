"""packman requirements class."""

from pipeline.tasks.requirements import task_requirement_base


class PackmanRequirements(task_requirement_base.TaskRequirementBase):

    @classmethod
    def require(cls):
        """Packman is gen-api-package."""
        return ['gen-api-package']

    @classmethod
    def install(cls):
        raise Exception('gen-api-package not installed')
