# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Factory function that recreates pipeline based on pipeline name and
kwargs."""


from artman.pipelines import pipeline_base
# These are required to list the subclasses of pipeline_base
from artman.pipelines import sample_pipeline
from artman.pipelines import gapic_generation
from artman.pipelines import grpc_generation
from artman.pipelines import core_generation
from artman.pipelines import batch_generation
from artman.utils.logger import logger

__all__ = (
    'batch_generation', 'core_generation', 'gapic_generation',
    'grpc_generation', 'make_pipeline', 'make_pipeline_flow',
    'pipeline_base', 'sample_pipeline',
)


def make_pipeline_flow(pipeline_name, remote_mode=False, **kwargs):
    """Factory function to make a GAPIC pipeline.

    Because the GAPIC pipeline is using OpenStack Taskflow, this factory
    function is expected to be a function (or staticmethod) which is
    reimportable (aka has a well defined name that can be located by the
    __import__ function in python, this excludes lambda style functions and
    instance methods). The factory function name will be saved into the
    logbook, and it will be imported and called to create the workflow objects
    (or recreate it if resumption happens).  This allows for the pipeline to be
    recreated if and when that is needed (even on remote machines, as long as
    the reimportable name can be located).

    """
    return make_pipeline(pipeline_name, remote_mode, **kwargs).flow


def make_pipeline(pipeline_name, remote_mode=False, **kwargs):
    for cls in _rec_subclasses(pipeline_base.PipelineBase):
        if cls.__name__ == pipeline_name:
            logger.info("Create %s instance." % pipeline_name)
            return cls(remote_mode=remote_mode, **kwargs)
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
