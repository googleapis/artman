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

"""Pipelines that run GAPIC code generation."""

from __future__ import absolute_import

from artman.pipelines import code_generation as code_gen
from artman.pipelines import grpc_generation as grpc_gen
from artman.tasks import emit_success
from artman import tasks
from artman.utils import task_utils


# kwargs required by GAPIC code gen
_GAPIC_REQUIRED = ['service_yaml', 'gapic_yaml', 'language', 'aspect']

_DISCOGAPIC_REQUIRED = ['gapic_yaml', 'language']


class GapicConfigPipeline(code_gen.CodeGenerationPipelineBase):

    def __init__(self, **kwargs):
        super(GapicConfigPipeline, self).__init__(
            GapicConfigTaskFactory(), **kwargs)

class DiscoGapicConfigPipeline(code_gen.CodeGenerationPipelineBase):

    def __init__(self, **kwargs):
        super(DiscoGapicConfigPipeline, self).__init__(
            DiscoGapicConfigTaskFactory(), **kwargs)

class GapicConfigTaskFactory(code_gen.TaskFactoryBase):

    def get_tasks(self, **kwargs):
        return task_utils.instantiate_tasks([
            tasks.protoc.ProtoDescGenTask,
            tasks.gapic.GapicConfigGenTask,
            tasks.gapic.GapicConfigMoveTask
        ], kwargs)

    def get_validate_kwargs(self):
        return code_gen.COMMON_REQUIRED

    def get_invalid_kwargs(self):
        return ['language']


class DiscoGapicConfigTaskFactory(code_gen.TaskFactoryBase):

    def get_tasks(self, **kwargs):
        return task_utils.instantiate_tasks([
            tasks.gapic.DiscoGapicConfigGenTask,
            tasks.gapic.GapicConfigMoveTask
        ], kwargs)

    def get_validate_kwargs(self):
        return code_gen.COMMON_DISCO_REQUIRED

    def get_invalid_kwargs(self):
        return ['language']


class GapicOnlyClientPipeline(code_gen.CodeGenerationPipelineBase):
    """The pipeline for generating a GAPIC_ONLY layer, other layers
    (like PROTOBUF or GRPC) will not be generated.
    """
    def __init__(self, language, **kwargs):
        super(GapicOnlyClientPipeline, self).__init__(
            GapicOnlyTaskFactory(),
            language=language,
            **kwargs
        )


class GapicClientPipeline(code_gen.CodeGenerationPipelineBase):
    """The pipeline for generating a complete GAPIC.

    This is intended to be the only command that needs to run to generate
    a complete GAPIC.
    """
    def __init__(self, language, **kwargs):
        super(GapicClientPipeline, self).__init__(
            GapicTaskFactory(),
            language=language,
            **kwargs
        )


class DiscoGapicClientPipeline(code_gen.CodeGenerationPipelineBase):
    """The pipeline for generating a complete GAPIC from a Discovery document.

    This is intended to be the only command that needs to run to generate
    a complete GAPIC.
    """
    def __init__(self, language, **kwargs):
        super(DiscoGapicClientPipeline, self).__init__(
            DiscoGapicTaskFactory(),
            language=language,
            **kwargs
        )

class CSharpPackagingTaskFactory(code_gen.TaskFactoryBase):

    def get_tasks(self, **kwargs):
        return [
            tasks.gapic.CSharpGapicPackagingTask
        ]

    def get_validate_kwargs(self):
        return ['gapic_code_dir', 'grpc_code_dir', 'proto_code_dir', 'gapic_yaml']

    def get_invalid_kwargs(self):
        return []


PACKAGING_TASK_FACTORY_DICT = {
    'csharp': CSharpPackagingTaskFactory
}

class GapicTaskFactory(code_gen.TaskFactoryBase):
    """A task factory describing GAPIC generation tasks.

    Language specific tasks may be defined in language-specific methods
    on this class.
    """
    def get_tasks(self, **kwargs):
        """Return the full list of instantiated tasks to generate a GAPIC.

        Args:
            kwargs (dict): Keyword arguments, which are passed through.
        """
        # Note: For languages where generating a GAPIC implies also generating
        # the GRPC or Proto library, we still generate the GAPIC _first_, even
        # though the GRPC is the dependency. This is because in some languages,
        # the GRPC is "tucked into" the GAPIC, and that process is much easier
        # if the code is generated in this order.
        answer = []

        if 'gapic_code_dir' in kwargs:
            answer = self._get_gapic_codegen_tasks(**kwargs)

        for grpc_task in self._get_grpc_codegen_tasks(**kwargs):
            if grpc_task not in answer:
                answer.append(grpc_task)

        for packaging_task in self._get_packaging_tasks(**kwargs):
            if packaging_task not in answer:
                answer.append(packaging_task)

        answer += emit_success.TASKS
        return task_utils.instantiate_tasks(answer, kwargs)

    def _get_gapic_codegen_tasks(self, language, **kwargs):
        """Return the code generation tasks necessary for creating a GAPIC.

        Args:
            language (str): The language.

        Returns:
            list: A list of Task subclasses.
        """
        return [
            tasks.protoc.ProtoDescGenTask,
            tasks.package_metadata.PackageMetadataConfigGenTask,
            tasks.gapic.GapicCodeGenTask,
            tasks.format.get_format_task(language),
        ]

    def _get_grpc_codegen_tasks(self, language, **kw):
        """Return the code generation tasks for making a GRPC package.

        Args:
            language (str): The language code is being generated in.
            kw (dict): Additional keyword arguments passed through to the
                grpc codegen task factory.

        Returns:
            list: A list of Task subclasses defined by the GRPC task factory.
        """

        grpc_factory = grpc_gen.ProtoGenTaskFactory(gen_grpc=True,
                                                    language=language, **kw)
        return grpc_factory.get_grpc_codegen_tasks(**kw)

    def _get_packaging_tasks(self, language, **kw):
        """Return the code generation tasks for packaging

        Args:
            language (str): The language code is being generated in.
            kw (dict): Additional keyword arguments passed through to the
                proto codegen task factory.

        Returns:
            list: A list of Task subclasses defined by the packaging task factory.
        """
        if language in PACKAGING_TASK_FACTORY_DICT:
            packaging_factory = PACKAGING_TASK_FACTORY_DICT[language]()
            return packaging_factory.get_tasks()
        return []

    def get_validate_kwargs(self):
        return _GAPIC_REQUIRED + code_gen.COMMON_REQUIRED

    def get_invalid_kwargs(self):
        return []


class DiscoGapicTaskFactory(code_gen.TaskFactoryBase):
    """A task factory describing GAPIC generation tasks on Discovery docs.

    Language specific tasks may be defined in language-specific methods
    on this class.
    """
    def get_tasks(self, **kwargs):
        """Return the full list of instantiated tasks to generate a GAPIC.

        Args:
            kwargs (dict): Keyword arguments, which are passed through.
        """
        answer = []

        if 'gapic_code_dir' in kwargs:
            answer = self._get_gapic_codegen_tasks(**kwargs)

        for packaging_task in self._get_packaging_tasks(**kwargs):
            if packaging_task not in answer:
                answer.append(packaging_task)

        answer += emit_success.TASKS
        return task_utils.instantiate_tasks(answer, kwargs)

    def _get_gapic_codegen_tasks(self, language, **kwargs):
        """Return the code generation tasks necessary for creating a GAPIC
        from a Discovery document.

        Args:
            language (str): The language.

        Returns:
            list: A list of Task subclasses.
        """
        return [
            tasks.io.PrepareOutputDirectoryTask,
            tasks.package_metadata.PackageMetadataConfigGenTask,
            tasks.gapic.DiscoGapicCodeGenTask,
            tasks.format.get_format_task(language),
        ]

    def _get_packaging_tasks(self, language, **kw):
        """Return the code generation tasks for packaging

        Args:
            language (str): The language code is being generated in.
            kw (dict): Additional keyword arguments passed through to the
                proto codegen task factory.

        Returns:
            list: A list of Task subclasses defined by the packaging task factory.
        """
        if language in PACKAGING_TASK_FACTORY_DICT:
            packaging_factory = PACKAGING_TASK_FACTORY_DICT[language]()
            return packaging_factory.get_tasks()
        return []

    def get_validate_kwargs(self):
        return _DISCOGAPIC_REQUIRED + code_gen.COMMON_DISCO_REQUIRED

    def get_invalid_kwargs(self):
        return []


class GapicOnlyTaskFactory(GapicTaskFactory):
    """A task factory describing GAPIC_ONLY generation tasks."""
    def _get_grpc_codegen_tasks(self, **kw):
        return[]

    def _get_packaging_tasks(self, **kw):
        return []
