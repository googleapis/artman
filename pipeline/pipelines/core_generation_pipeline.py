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
   language contains the well known types, defined by protobuf, for that
   language."""

from pipeline.pipelines import code_generation_pipeline
from pipeline.pipelines import grpc_generation_pipeline
from pipeline.tasks import protoc_tasks
from pipeline.tasks import publish_tasks


class JavaCoreProtoPipeline(grpc_generation_pipeline.GrpcClientPipeline):
    """Generates a package with the common protos from googleapis.

    It inherits from GrpcClientPipeline because it uses Packman just like
    client generation does; the only difference is the extra
    --build_common_protos argument to Packman.
    """

    def __init__(self, **kwargs):
        kwargs['language'] = 'java'
        packman_flags = ['--experimental_alt_java', '--build_common_protos']
        kwargs.update({'packman_flags': packman_flags})
        super(JavaCoreProtoPipeline, self).__init__(**kwargs)

    def get_grpc_publish_tasks(self, **kwargs):
        return [publish_tasks.MavenDeployTask('MavenDeploy', inject=kwargs)]


class GoCoreProtoPipeline(code_generation_pipeline.CodeGenerationPipelineBase):
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
        flow = super(GoCoreProtoPipeline, self).do_build_flow(**kwargs)
        flow.add(
            protoc_tasks.ProtoCodeGenTask('CoreProtoGen',
                                          inject=kwargs),
            protoc_tasks.GoExtractImportBaseTask('ExtractGoPackageName',
                                                 inject=kwargs),
            protoc_tasks.GoLangUpdateImportsTask('UpdateImports',
                                                 inject=kwargs))
        return flow

    def validate_kwargs(self, **kwargs):
        code_generation_pipeline._validate_codegen_kwargs(
            ['gapic_api_yaml', 'final_repo_dir'],
            **kwargs)


class CSharpCorePipeline(code_generation_pipeline.CodeGenerationPipelineBase):

    def __init__(self, **kwargs):
        kwargs['language'] = 'csharp'
        super(CSharpCorePipeline, self).__init__(**kwargs)

    def do_build_flow(self, **kwargs):
        flow = super(CSharpCorePipeline, self).do_build_flow(**kwargs)
        flow.add(protoc_tasks.ProtoCodeGenTask('ProtoGen', inject=kwargs))
        return flow
