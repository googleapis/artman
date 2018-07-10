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

"""Base class for pipeline."""

from taskflow.flow import Flow
from taskflow.patterns import linear_flow


class PipelineBase(object):
    """Base class of pipeline.

    Subclasses must implement validate_kwargs and do_build_flow methods.
    """

    def __init__(self, **kwargs):
        self._kwargs = kwargs
        self._flow = self.build_flow(**kwargs)

    def build_flow(self, **kwargs):
        """Make the task flow based on kwargs."""
        self.validate_kwargs(**kwargs)

        # Call do_make_flow implemented by subclass to make the flow.
        flow = self.do_build_flow(**kwargs)
        if not isinstance(flow, Flow):
            raise TypeError('Return type must be taskflow.flow.Flow.')

        return flow

    def validate_kwargs(self, **kwargs):
        """Abstract method, subclass must implement this method to validate
        kwargs.
        """
        raise NotImplementedError('Subclass must implement abstract method')

    def do_build_flow(self, **kwargs):
        """Abstract method, subclass must implment this method and return a task
        instance.
        """
        raise NotImplementedError('Subclass must implement abstract method')

    @property
    def flow(self):
        return self._flow

    @property
    def name(self):
        return self.__class__.__name__

    @property
    def kwargs(self):
        return self._kwargs


class EmptyPipeline(PipelineBase):

    def do_build_flow(self, **kwargs):
        flow = linear_flow.Flow('empty-pipeline')
        return flow

    def validate_kwargs(self, **kwargs):
        pass
