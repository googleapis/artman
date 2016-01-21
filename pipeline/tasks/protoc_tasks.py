"""Tasks related to protoc"""

import os
import subprocess
from taskflow import task
from pipeline.tasks import task_base
from pipeline.tasks.requirements import grpc_requirements


class ProtoDescriptorGenTask(task_base.TaskBase):
    """Generates proto descriptor set"""
    default_provides = 'descriptor_set'

    def execute(self, proto_path, service_protos, core_proto_path, output_dir):
        print 'Compiling descriptors {0}'.format(service_protos)
        out_file = 'descriptor.desc'
        subprocess.call(['mkdir', '-p', output_dir])
        subprocess.call(['protoc',
                         '--include_imports',
                         '--proto_path=' + proto_path,
                         '--proto_path=' + core_proto_path,
                         '--include_source_info',
                         '-o', os.path.join(output_dir, out_file)]
                        + service_protos)
        return os.path.join(output_dir, out_file)

    def requires():
        return [grpc_requirement.GrpcRequirement]


class GrpcCodeGenTask(task_base.TaskBase):
    """Generates the gRPC client library"""
    def execute(self, plugin, proto_path, core_proto_path, output_dir):
        protos = []
        for root, _, files in os.walk(proto_path):
            protos += [os.path.join(root, proto) for proto in files
                       if os.path.splitext(proto)[1] == '.proto']
        for proto in protos:
            subprocess.call(
                ['protoc', '--proto_path=' + proto_path,
                 '--proto_path=' + core_proto_path, '--python_out=' + output_dir,
                 '--plugin=protoc-gen-grpc=' +
                 subprocess.check_output(['which', plugin])[:-1],
                 '--grpc_out=' + output_dir, proto])
            print 'Running protoc on {0}'.format(proto)

    def requires():
        return [grpc_requirement.GrpcRequirements]
