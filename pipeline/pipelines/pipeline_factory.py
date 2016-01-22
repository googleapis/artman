"""Factory function that recreates pipeline based on pipeline name and
kwargs."""

from pipeline.pipelines import pipeline_base
from pipeline.pipelines import sample_pipeline
from pipeline.pipelines import code_generation_pipeline


def make_pipeline_flow(pipeline_name, **kwargs):
    """This factory function to make veneer pipeline.

    Because veneer pipeline is using OpenStack Taskflow, this factory function
    is expected to be a function (or staticmethod) which is reimportable (aka
    has a well defined name that can be located by the __import__ function in
    python, this excludes lambda style functions and instance methods). The
    factory function name will be saved into the logbook, and it will be
    imported and called to create the workflow objects (or recreate it if
    resumption happens).  This allows for the pipeline to be recreated if and
    when that is needed (even on remote machines, as long as the reimportable
    name can be located).

    """
    return make_pipeline(pipeline_name, **kwargs).flow


def make_pipeline(pipeline_name, **kwargs):
    for cls in _rec_subclasses(pipeline_base.PipelineBase):
        if cls.__name__ == pipeline_name:
            print("Create %s instance." % pipeline_name)
            return cls(**kwargs)
    raise ValueError("Invalid pipeline name: %s" % pipeline_name)


def _rec_subclasses(cls):
    """Returns all recursive subclasses of a given class (i.e., subclasses,
    sub-subclasses, etc.)"""
    subclasses = []
    if cls.__subclasses__():
        for subcls in cls.__subclasses__():
            subclasses.append(subcls)
            subclasses += _rec_subclasses(subcls)
    return subclasses
