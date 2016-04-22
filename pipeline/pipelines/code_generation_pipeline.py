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

"""Pipelines that run gRPC codegen and VGen"""

import os
from pipeline.pipelines import pipeline_base
from pipeline.tasks import protoc_tasks, gapic_tasks, format_tasks
from pipeline.utils import pipeline_util
from taskflow.patterns import linear_flow


# kwargs required by GAPIC code gen
_VGEN_REQUIRED = ['service_yaml',
                  'gapic_language_yaml',
                  'gapic_api_yaml',
                  'auto_merge',
                  'auto_resolve',
                  'ignore_base',
                  'final_repo_dir']


def _validate_toolkit_path(toolkit_path):
    if not (os.path.isfile(
                os.path.join(toolkit_path, 'gradlew')) and
            os.path.isfile(
                os.path.join(toolkit_path, 'build.gradle'))):
        raise ValueError(
                'toolkit repo does not contain `gradlew` or `build.gradle`'
                'at {0}'.format(toolkit_path))


# TODO(garrettjones) fix required to be relative to pipeline.
# Ideally this should just be computed dynamically based
# on the pipeline's tasks.
def _validate_codegen_kwargs(extra_args, **kwargs):
    required = ['src_proto_path',
                'import_proto_path',
                'toolkit_path',
                'output_dir',
                'language',
                'api_name']
    pipeline_util.validate_exists(required + extra_args, **kwargs)
    _validate_toolkit_path(kwargs['toolkit_path'])


class GapicConfigPipeline(pipeline_base.PipelineBase):

    def __init__(self, **kwargs):
        kwargs['language'] = ''
        super(GapicConfigPipeline, self).__init__(**kwargs)

    def do_build_flow(self, **kwargs):
        flow = linear_flow.Flow('gapic-configgen')
        flow.add(protoc_tasks.ProtoDescGenTask('ProtoDesc', inject=kwargs),
                 gapic_tasks.GapicConfigGenTask(
                     'GapicConfigGen', inject=kwargs),
                 gapic_tasks.GapicConfigMoveTask(
                     'GapicConfigMove', inject=kwargs))
        return flow

    def validate_kwargs(self, **kwargs):
        _validate_codegen_kwargs([], **kwargs)


class PythonGrpcClientPipeline(pipeline_base.PipelineBase):

    def __init__(self, **kwargs):
        kwargs['language'] = 'python'
        super(PythonGrpcClientPipeline, self).__init__(**kwargs)

    def do_build_flow(self, **kwargs):
        flow = linear_flow.Flow('grpc-codegen')
        flow.add(protoc_tasks.GrpcPackmanTask('Packman', inject=kwargs))
        return flow

    def validate_kwargs(self, **kwargs):
        _validate_codegen_kwargs([], **kwargs)


class PythonGapicClientPipeline(pipeline_base.PipelineBase):

    def __init__(self, **kwargs):
        kwargs['language'] = 'python'
        super(PythonGapicClientPipeline, self).__init__(**kwargs)

    def do_build_flow(self, **kwargs):
        flow = linear_flow.Flow('gapic-codegen')
        flow.add(protoc_tasks.ProtoDescGenTask('ProtoDesc', inject=kwargs),
                 gapic_tasks.GapicCodeGenTask('GapicCodegen',
                                              inject=kwargs),
                 format_tasks.PythonFormatTask('PythonFormat', inject=kwargs)
                 # TODO: Add merge task for python here.
                 )
        return flow

    def validate_kwargs(self, **kwargs):
        _validate_codegen_kwargs(_VGEN_REQUIRED, **kwargs)


class RubyGrpcClientPipeline(pipeline_base.PipelineBase):

    def __init__(self, **kwargs):
        kwargs['language'] = 'ruby'
        super(RubyGrpcClientPipeline, self).__init__(**kwargs)

    def do_build_flow(self, **kwargs):
        flow = linear_flow.Flow('grpc-codegen')
        flow.add(protoc_tasks.GrpcPackmanTask('Packman', inject=kwargs))
        return flow

    def validate_kwargs(self, **kwargs):
        _validate_codegen_kwargs([], **kwargs)


class RubyGapicClientPipeline(pipeline_base.PipelineBase):

    def __init__(self, **kwargs):
        kwargs['language'] = 'ruby'
        super(RubyGapicClientPipeline, self).__init__(**kwargs)

    def do_build_flow(self, **kwargs):
        flow = linear_flow.Flow('gapic-codegen')
        flow.add(protoc_tasks.ProtoDescGenTask('ProtoDesc', inject=kwargs),
                 gapic_tasks.GapicCodeGenTask('GapicCodegen',
                                              inject=kwargs),
                 format_tasks.RubyFormatTask('RubyFormat', inject=kwargs),
                 # TODO: Add merge task for ruby here.
                 )
        return flow

    def validate_kwargs(self, **kwargs):
        _validate_codegen_kwargs(_VGEN_REQUIRED, **kwargs)


class JavaCorePipeline(pipeline_base.PipelineBase):

    def __init__(self, **kwargs):
        kwargs['language'] = 'java'
        super(JavaCorePipeline, self).__init__(**kwargs)

    def do_build_flow(self, **kwargs):
        flow = linear_flow.Flow('core-codegen')
        flow.add(protoc_tasks.ProtoCodeGenTask('ProtoGen', inject=kwargs))
        return flow

    def validate_kwargs(self, **kwargs):
        _validate_codegen_kwargs([], **kwargs)


class JavaGrpcClientPipeline(pipeline_base.PipelineBase):

    def __init__(self, **kwargs):
        kwargs['language'] = 'java'
        super(JavaGrpcClientPipeline, self).__init__(**kwargs)

    def do_build_flow(self, **kwargs):
        flow = linear_flow.Flow('grpc-codegen')
        flow.add(protoc_tasks.ProtoCodeGenTask('ProtoGen', inject=kwargs),
                 protoc_tasks.GrpcCodeGenTask('GrpcCodegen', inject=kwargs))
        return flow

    def validate_kwargs(self, **kwargs):
        _validate_codegen_kwargs([], **kwargs)


class JavaGapicClientPipeline(pipeline_base.PipelineBase):

    def __init__(self, **kwargs):
        kwargs['language'] = 'java'
        super(JavaGapicClientPipeline, self).__init__(**kwargs)

    def do_build_flow(self, **kwargs):
        flow = linear_flow.Flow('gapic-codegen')
        flow.add(protoc_tasks.ProtoDescGenTask('ProtoDesc', inject=kwargs),
                 gapic_tasks.GapicCodeGenTask('GapicCodegen',
                                              inject=kwargs),
                 format_tasks.JavaFormatTask('JavaFormat', inject=kwargs),
                 gapic_tasks.GapicMergeTask('GapicMerge', inject=kwargs))
        return flow

    def validate_kwargs(self, **kwargs):
        _validate_codegen_kwargs(_VGEN_REQUIRED, **kwargs)


class GoCoreProtoPipeline(pipeline_base.PipelineBase):
    """Responsible for the protobuf flow for Go language.

    The Go compiler needs to specify an import path which is relative to
    $GOPATH/src, otherwise it can't find the package. Therefore,
    the import path in proto files needs to be modified in this manner,
    which is taken care of by GoLangUpdateProtoImportsTask.

    TODO(mukai): Remove this flow once the repository for well-known types is
    set up.
    """

    def __init__(self, **kwargs):
        kwargs['language'] = 'go'
        super(GoCoreProtoPipeline, self).__init__(**kwargs)

    def do_build_flow(self, **kwargs):
        flow = linear_flow.Flow('core-protogen')
        flow.add(
            protoc_tasks.ProtoCodeGenTask('CoreProtoGen',
                                          inject=kwargs),
            gapic_tasks.GoExtractImportBaseTask('ExtractGoPackageName',
                                                inject=kwargs),
            protoc_tasks.GoLangUpdateImportsTask('UpdateImports',
                                                 inject=kwargs))
        return flow

    def validate_kwargs(self, **kwargs):
        # gapic_api_yaml is required by GoExtractImportBaseTask to provide
        # the import path base needed by GoLangUpdateImportsTask.
        _validate_codegen_kwargs(['gapic_api_yaml', 'final_repo_dir'],
                                 **kwargs)


class GoGrpcClientPipeline(pipeline_base.PipelineBase):
    """Responsible for the protobuf/grpc flow for Go language.

    The Go compiler needs to specify an import path which is relative to
    $GOPATH/src, otherwise it can't find the package. Therefore,
    the import path in proto files needs to be modified in this manner,
    which is taken care of by GoLangUpdateProtoImportsTask.
    """

    def __init__(self, **kwargs):
        kwargs['language'] = 'go'
        super(GoGrpcClientPipeline, self).__init__(**kwargs)

    def do_build_flow(self, **kwargs):
        flow = linear_flow.Flow('grpc-protogen')
        flow.add(
            protoc_tasks.ProtoAndGrpcCodeGenTask('GrpcCodegen',
                                                 inject=kwargs),
            gapic_tasks.GoExtractImportBaseTask('ExtractGoPackageName',
                                                inject=kwargs),
            protoc_tasks.GoLangUpdateImportsTask('UpdateImports',
                                                 inject=kwargs))
        return flow

    def validate_kwargs(self, **kwargs):
        # gapic_api_yaml is required by GoExtractImportBaseTask to provide
        # the import path base needed by GoLangUpdateImportsTask.
        _validate_codegen_kwargs(['gapic_api_yaml', 'final_repo_dir'],
                                 **kwargs)


class GoGapicClientPipeline(pipeline_base.PipelineBase):

    def __init__(self, **kwargs):
        kwargs['language'] = 'go'
        super(GoGapicClientPipeline, self).__init__(**kwargs)

    def do_build_flow(self, **kwargs):
        flow = linear_flow.Flow('gapic-codegen')
        flow.add(protoc_tasks.ProtoDescGenTask('ProtoDescGen',
                                               inject=kwargs),
                 gapic_tasks.GapicCodeGenTask('GapicCodegen',
                                              inject=kwargs),
                 format_tasks.GoFormatTask('GoFormat', inject=kwargs),
                 gapic_tasks.GapicMergeTask('GapicMerge', inject=kwargs))
        return flow

    def validate_kwargs(self, **kwargs):
        _validate_codegen_kwargs(_VGEN_REQUIRED, **kwargs)


class CSharpCorePipeline(pipeline_base.PipelineBase):

    def __init__(self, **kwargs):
        kwargs['language'] = 'csharp'
        super(CSharpCorePipeline, self).__init__(**kwargs)

    def do_build_flow(self, **kwargs):
        flow = linear_flow.Flow('core-codegen')
        flow.add(protoc_tasks.ProtoCodeGenTask('ProtoGen', inject=kwargs))
        return flow

    def validate_kwargs(self, **kwargs):
        _validate_codegen_kwargs([], **kwargs)


class CSharpGrpcClientPipeline(pipeline_base.PipelineBase):

    def __init__(self, **kwargs):
        kwargs['language'] = 'csharp'
        super(CSharpGrpcClientPipeline, self).__init__(**kwargs)

    def do_build_flow(self, **kwargs):
        flow = linear_flow.Flow('grpc-codegen')
        flow.add(protoc_tasks.ProtoCodeGenTask('ProtoGen', inject=kwargs),
                 protoc_tasks.GrpcCodeGenTask('GrpcCodegen', inject=kwargs))
        return flow

    def validate_kwargs(self, **kwargs):
        _validate_codegen_kwargs([], **kwargs)


class CSharpGapicClientPipeline(pipeline_base.PipelineBase):

    def __init__(self, **kwargs):
        kwargs['language'] = 'csharp'
        super(CSharpGapicClientPipeline, self).__init__(**kwargs)

    def do_build_flow(self, **kwargs):
        flow = linear_flow.Flow('gapic-codegen')
        flow.add(protoc_tasks.ProtoDescGenTask('ProtoDesc', inject=kwargs),
                 gapic_tasks.GapicCodeGenTask('GapicCodegen',
                                              inject=kwargs))
        return flow

    def validate_kwargs(self, **kwargs):
        _validate_codegen_kwargs(_VGEN_REQUIRED, **kwargs)
