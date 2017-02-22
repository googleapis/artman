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

"""Pipelines that run GAPIC"""

from pipeline.pipelines import code_generation_pipeline as code_gen
from pipeline.pipelines import batch_generation_pipeline as batch_gen
from pipeline.tasks import (gapic_tasks, format_tasks, package_metadata_tasks,
                            protoc_tasks, staging_tasks)
from pipeline.utils import task_utils


# kwargs required by GAPIC code gen
_GAPIC_REQUIRED = ['service_yaml', 'gapic_language_yaml', 'gapic_api_yaml',
                   'final_repo_dir', 'language', 'stage_output']


class GapicConfigPipeline(code_gen.CodeGenerationPipelineBase):

    def __init__(self, **kwargs):
        super(GapicConfigPipeline, self).__init__(
            GapicConfigTaskFactory(), **kwargs)


class GapicConfigTaskFactory(code_gen.TaskFactoryBase):

    def get_tasks(self, **kwargs):
        return task_utils.instantiate_tasks([protoc_tasks.ProtoDescGenTask,
                                             gapic_tasks.GapicConfigGenTask,
                                             gapic_tasks.GapicConfigMoveTask],
                                            kwargs)

    def get_validate_kwargs(self):
        return code_gen.COMMON_REQUIRED

    def get_invalid_kwargs(self):
        return ['language']


class GapicClientPipeline(code_gen.CodeGenerationPipelineBase):

    def __init__(self, **kwargs):
        super(GapicClientPipeline, self).__init__(
            get_gapic_task_factory(kwargs['language']),
            **kwargs)


class GapicClientBatchPipeline(batch_gen.BatchPipeline):

    def __init__(self, **kwargs):
        super(GapicClientBatchPipeline, self).__init__(
            _make_batch_pipeline_tasks, **kwargs)


def _make_batch_pipeline_tasks(**kwargs):
    task_factory = get_gapic_task_factory(kwargs['language'])
    tasks = (task_factory._get_gapic_codegen_tasks(**kwargs)
             + task_factory._get_gapic_staging_tasks(**kwargs))
    return task_utils.instantiate_tasks(tasks, kwargs)


class GapicTaskFactoryBase(code_gen.TaskFactoryBase):

    def get_tasks(self, **kwargs):
        tasks = (self._get_gapic_codegen_tasks(**kwargs)
                 + self._get_gapic_staging_tasks(**kwargs)
                 + self._get_gapic_package_tasks(**kwargs))
        return task_utils.instantiate_tasks(tasks, kwargs)

    def _get_gapic_codegen_tasks(self, **kwargs):
        return [protoc_tasks.ProtoDescGenTask,
                package_metadata_tasks.PackageMetadataConfigGenTask,
                gapic_tasks.GapicCodeGenTask,
                format_tasks.get_format_task(kwargs['language'])]

    def _get_gapic_staging_tasks(self, **kwargs):
        if kwargs['stage_output']:
            return [staging_tasks.StagingOutputDirTask,
                    staging_tasks.StagingCleanTask,
                    staging_tasks.StagingCopyTask]
        return []

    def _get_gapic_package_tasks(self, **kwargs):
        return [gapic_tasks.GapicCopyTask]

    def get_validate_kwargs(self):
        return _GAPIC_REQUIRED + code_gen.COMMON_REQUIRED

    def get_invalid_kwargs(self):
        return []


class _PythonGapicTaskFactory(GapicTaskFactoryBase):

    def _get_gapic_package_tasks(self, **kwargs):
        return [
            gapic_tasks.GapicCleanTask,
            gapic_tasks.GapicCopyTask,
        ]


class _RubyGapicTaskFactory(GapicTaskFactoryBase):

    def _get_gapic_package_tasks(self, **kwargs):
        return [gapic_tasks.GapicCopyTask]


class _NodeJSGapicTaskFactory(GapicTaskFactoryBase):

    def _get_gapic_package_tasks(self, **kwargs):
        return [gapic_tasks.GapicCopyTask,
                gapic_tasks.GapicPackmanTask]


_GAPIC_TASK_FACTORY_DICT = {
    'java': GapicTaskFactoryBase,
    'python': _PythonGapicTaskFactory,
    'go': GapicTaskFactoryBase,
    'ruby': _RubyGapicTaskFactory,
    'php': GapicTaskFactoryBase,
    'csharp': GapicTaskFactoryBase,
    'nodejs': _NodeJSGapicTaskFactory
}


def get_gapic_task_factory(language):
    cls = _GAPIC_TASK_FACTORY_DICT.get(language)
    if cls:
        return cls()
    else:
        raise ValueError('No GAPIC task factory found for language: '
                         + language)
