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

"""Pipelines that run protoc core codegen. The generated core library for each
language contains the well known types, defined by protobuf, for that language.
"""

from artman.pipelines import code_generation as code_gen
from artman.tasks import protoc_tasks
from artman.tasks import package_metadata_tasks
from artman.utils import task_utils


class CoreProtoPipeline(code_gen.CodeGenerationPipelineBase):

    def __init__(self, **kwargs):
        super(CoreProtoPipeline, self).__init__(
            get_core_task_factory(kwargs['language']), **kwargs)


class CoreTaskFactoryBase(code_gen.TaskFactoryBase):

    def get_tasks(self, **kwargs):
        return task_utils.instantiate_tasks(
            self._get_core_codegen_tasks(**kwargs), kwargs)

    def _get_core_codegen_tasks(self, **kwargs):
        raise NotImplementedError('Subclass must implement abstract method')

    def get_validate_kwargs(self):
        return code_gen.COMMON_REQUIRED

    def get_invalid_kwargs(self):
        return []


class _GoCoreTaskFactory(CoreTaskFactoryBase):
    """Responsible for the protobuf flow for Go language."""

    def _get_core_codegen_tasks(self, **kwargs):
        return [
            protoc_tasks.ProtoCodeGenTask,
            protoc_tasks.GoCopyTask,
        ]

    def get_validate_kwargs(self):
        return ['gapic_yaml', 'gapic_code_dir'] + code_gen.COMMON_REQUIRED


class _CSharpCoreTaskFactory(CoreTaskFactoryBase):

    def _get_core_codegen_tasks(self, **kwargs):
        return [protoc_tasks.ProtoCodeGenTask]


class _JavaCoreTaskFactory(CoreTaskFactoryBase):
    """Responsible for the core protobuf flow for Java language."""

    def _get_core_codegen_tasks(self, **kwargs):
        return [protoc_tasks.ProtoDescGenTask,
                protoc_tasks.ProtoCodeGenTask,
                package_metadata_tasks.PackageMetadataConfigGenTask,
                package_metadata_tasks.ProtoPackageMetadataGenTask,
                protoc_tasks.JavaProtoCopyTask]


_CORE_TASK_FACTORY_DICT = {
    'go': _GoCoreTaskFactory,
    'csharp': _CSharpCoreTaskFactory,
    'java': _JavaCoreTaskFactory,
}


def get_core_task_factory(language):
    cls = _CORE_TASK_FACTORY_DICT.get(language)
    if cls:
        return cls()
    else:
        raise ValueError('No core task factory found for language: '
                         + language)
