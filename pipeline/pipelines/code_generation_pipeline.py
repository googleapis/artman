"""Pipelines that run gRPC codegen and VGen"""

import os
from pipeline.pipelines import pipeline_base
from pipeline.tasks import protoc_tasks, veneer_tasks
from pipeline.utils import pipeline_util
from taskflow.patterns import linear_flow


class CodeGenPipeline(pipeline_base.PipelineBase):

    def __init__(self, **kwargs):
        super(CodeGenPipeline, self).__init__(**kwargs)

    def do_build_flow(self, **kwargs):
        flow = linear_flow.Flow('codegen')
        flow.add(protoc_tasks.ProtoDescriptorGenTask('ProtoCompilation',
                                                     inject=kwargs),
                 protoc_tasks.GrpcCodeGenTask('GrpcCodegen', inject=kwargs),
                 protoc_tasks.PackmanTask('Packman', inject=kwargs),
                 veneer_tasks.VeneerCodeGenTask('VeneerCodegen', inject=kwargs))
        return flow

    def validate_kwargs(self, **kwargs):
        required = ['service_proto_path',
                    'import_proto_path',
                    'gapi_tools_path',
                    'service_yaml',
                    'veneer_yaml',
                    'output_dir',
                    'plugin']
        pipeline_util.validate_exists(required, **kwargs)
        if not (os.path.isfile(
                    os.path.join(kwargs['gapi_tools_path'], 'gradlew')) and
                os.path.isfile(
                    os.path.join(kwargs['gapi_tools_path'], 'build.gradle'))):
            raise ValueError(
                'gapi-tools does not contain `gradlew` or' '`build.gradle`'
                'at {0}'.format(kwargs['gapi_tools_path']))



class PythonCodeGenPipeline(CodeGenPipeline):

    def __init__(self, **kwargs):
        kwargs['plugin'] = 'grpc_python_plugin'
        super(PythonCodeGenPipeline, self).__init__(**kwargs)
