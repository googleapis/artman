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

"""Tasks related to protoc"""

import io
import os
import re
from ruamel import yaml

import six

from artman.tasks import task_base
from artman.utils import task_utils
from artman.utils.logger import logger
from artman.utils import protoc_utils


class ProtoDescGenTask(task_base.TaskBase):
    """Generates proto descriptor set"""
    default_provides = 'descriptor_set'

    def execute(self, src_proto_path, import_proto_path, output_dir,
                api_name, api_version, organization_name, toolkit_path,
                root_dir, excluded_proto_path=[], proto_deps=[]):
        desc_proto_paths = []
        for dep in proto_deps:
            if 'proto_path' in dep and dep['proto_path']:
                desc_proto_paths.append(os.path.join(root_dir, dep['proto_path']))
        desc_protos = list(
            protoc_utils.find_protos(src_proto_path + desc_proto_paths,
                                     excluded_proto_path))
        header_proto_path = import_proto_path + desc_proto_paths
        header_proto_path.extend(src_proto_path)
        desc_out_file = task_utils.api_full_name(
            api_name, api_version, organization_name) + '.desc'
        logger.debug('Compiling descriptors for {0}'.format(desc_protos))
        self.exec_command(['mkdir', '-p', output_dir])
        # DescGen don't use _group_by_dirname right now because
        #   - it doesn't have to
        #   - and multiple invocation will overwrite the desc_out_file
        self.exec_command(
            ['protoc'] +
            protoc_utils.protoc_header_params(header_proto_path, toolkit_path) +
            protoc_utils.protoc_desc_params(output_dir, desc_out_file) +
            desc_protos)
        return os.path.join(output_dir, desc_out_file)


class ProtocCodeGenTaskBase(task_base.TaskBase):
    """Generates protos"""
    def _execute_proto_codegen(
            self, language, src_proto_path, import_proto_path,
            pkg_dir, api_name, api_version, organization_name,
            toolkit_path, gapic_yaml, gen_proto=False, gen_grpc=False,
            final_src_proto_path=None, final_import_proto_path=None,
            excluded_proto_path=[]):
        src_proto_path = final_src_proto_path or src_proto_path
        import_proto_path = final_import_proto_path or import_proto_path
        proto_params = protoc_utils.PROTO_PARAMS_MAP[language]

        if gen_proto:
            protoc_proto_params = protoc_utils.protoc_proto_params(
                proto_params, pkg_dir, gapic_yaml, with_grpc=True)
        else:
            protoc_proto_params = []

        if gen_grpc:
            protoc_grpc_params = protoc_utils.protoc_grpc_params(
                proto_params, pkg_dir, toolkit_path)
        else:
            protoc_grpc_params = []

        # protoc-gen-go has some peculiarities:
        # It can only compile one package per invocation. So, we need to split
        # proto files by packages.
        #
        # The order of the input files affects comments and internal variables.
        # While this doesn't affect the correctness of the result, we sort
        # proto files for reproducibility.
        #
        # Other languages don't mind us doing this, so we just do it for
        # everyone.
        for (dirname, protos) in protoc_utils.group_by_dirname(
                protoc_utils.find_protos(src_proto_path, excluded_proto_path)).items():
            # It is possible to get duplicate protos. De-dupe them.
            protos = sorted(set(protos))

            # Execute protoc.
            self.exec_command(proto_params.proto_compiler_command +
                protoc_utils.protoc_header_params(
                    import_proto_path + src_proto_path, toolkit_path) +
                protoc_proto_params +
                protoc_grpc_params +
                protos)

        return pkg_dir


class ProtoCodeGenTask(ProtocCodeGenTaskBase):
    default_provides = 'proto_code_dir'

    """Generates protos"""
    def execute(self, language, src_proto_path, import_proto_path,
                output_dir, api_name, api_version, organization_name,
                toolkit_path, gapic_yaml, final_src_proto_path=None,
                final_import_proto_path=None, excluded_proto_path=[]):
        pkg_dir = protoc_utils.prepare_proto_pkg_dir(
            output_dir, api_name, api_version, organization_name, language)
        return self._execute_proto_codegen(
            language, src_proto_path, import_proto_path, pkg_dir,
            api_name, api_version, organization_name, toolkit_path,
            gapic_yaml, gen_proto=True,
            final_src_proto_path=final_src_proto_path,
            final_import_proto_path=final_import_proto_path,
            excluded_proto_path=excluded_proto_path)


class GrpcCodeGenTask(ProtocCodeGenTaskBase):
    default_provides = 'grpc_code_dir'

    """Generates the gRPC client library"""
    def execute(self, language, src_proto_path, import_proto_path,
                toolkit_path, output_dir, api_name, api_version,
                organization_name, gapic_yaml, final_src_proto_path=None,
                final_import_proto_path=None, excluded_proto_path=[]):
        pkg_dir = protoc_utils.prepare_grpc_pkg_dir(
            output_dir, api_name, api_version, organization_name, language)
        return self._execute_proto_codegen(
            language, src_proto_path, import_proto_path, pkg_dir,
            api_name, api_version,  organization_name, toolkit_path,
            gapic_yaml, gen_grpc=True,
            final_src_proto_path=final_src_proto_path,
            final_import_proto_path=final_import_proto_path,
            excluded_proto_path=excluded_proto_path)


class ProtoAndGrpcCodeGenTask(ProtocCodeGenTaskBase):
    default_provides = 'grpc_code_dir'

    """Generates protos and the gRPC client library"""
    def execute(self, language, src_proto_path, import_proto_path,
                toolkit_path, output_dir, api_name, api_version,
                organization_name, gapic_yaml, final_src_proto_path=None,
                final_import_proto_path=None, excluded_proto_path=[]):
        pkg_dir = protoc_utils.prepare_grpc_pkg_dir(
            output_dir, api_name, api_version, organization_name, language)
        return self._execute_proto_codegen(
            language, src_proto_path, import_proto_path, pkg_dir,
            api_name, api_version, organization_name, toolkit_path,
            gapic_yaml, gen_proto=True, gen_grpc=True,
            final_src_proto_path=final_src_proto_path,
            final_import_proto_path=final_import_proto_path,
            excluded_proto_path=excluded_proto_path)


class GoCopyTask(task_base.TaskBase):
    def execute(self, gapic_code_dir, grpc_code_dir):
        for entry in os.listdir(grpc_code_dir):
            src_path = os.path.join(grpc_code_dir, entry)
            self.exec_command([
                'cp', '-rf', src_path, gapic_code_dir])


class RubyGrpcCopyTask(task_base.TaskBase):
    """Copies the generated protos and gRPC client library to
    the gapic_code_dir/lib.
    """
    def execute(self, api_name, api_version, language, organization_name,
                output_dir, gapic_code_dir, grpc_code_dir):
        final_output_dir = os.path.join(gapic_code_dir, 'lib')
        logger.info('Copying %s/* to %s.' % (grpc_code_dir, final_output_dir))
        if not os.path.exists(final_output_dir):
            self.exec_command(['mkdir', '-p', final_output_dir])
        for entry in sorted(os.listdir(grpc_code_dir)):
            src_path = os.path.join(grpc_code_dir, entry)
            self.exec_command([
                'cp', '-rf', src_path, final_output_dir])


class JavaProtoCopyTask(task_base.TaskBase):
    """Copies the .proto files into the grpc_code_dir directory
    """
    def execute(self, src_proto_path, proto_code_dir, excluded_proto_path=[]):
        grpc_proto_dir = os.path.join(proto_code_dir, 'src', 'main', 'proto')
        for proto_path in src_proto_path:
            index = protoc_utils.find_google_dir_index(proto_path)
            for src_proto_file in protoc_utils.find_protos(
                    [proto_path], excluded_proto_path):
                relative_proto_file = src_proto_file[index:]
                dst_proto_file = os.path.join(
                    grpc_proto_dir, relative_proto_file)
                self.exec_command(
                    ['mkdir', '-p', os.path.dirname(dst_proto_file)])
                self.exec_command(['cp', src_proto_file, dst_proto_file])


class PhpGrpcMoveTask(task_base.TaskBase):
    """Moves the generated protos and gRPC client library to
    the gapic_code_dir/proto directory.
    """
    default_provides = 'grpc_code_dir'

    def execute(self, grpc_code_dir, gapic_code_dir=None):
        if not gapic_code_dir:
            return grpc_code_dir
        final_output_dir = os.path.join(gapic_code_dir, 'proto')
        if not os.path.exists(final_output_dir):
            self.exec_command(['mkdir', '-p', final_output_dir])
        logger.info('Moving %s/* to %s.' % (grpc_code_dir, final_output_dir))
        for entry in sorted(os.listdir(grpc_code_dir)):
            src_path = os.path.join(grpc_code_dir, entry)
            self.exec_command([
                'mv', src_path, os.path.join(final_output_dir, entry)])
        self.exec_command([
            'rm', '-r', grpc_code_dir])
        return final_output_dir


# TODO (michaelbausor): Once correct naming is supported in
# gRPC, we should remove this.
class PhpGrpcRenameTask(task_base.TaskBase):
    """Rename references to proto files in the gRPC stub."""

    def execute(self, grpc_code_dir):
        for filename in protoc_utils.list_files_recursive(grpc_code_dir):
            if filename.endswith('GrpcClient.php'):
                logger.info('Performing replacements in: %s' % (filename,))
                with io.open(filename, encoding='UTF-8') as f:
                    contents = f.read()
                contents = protoc_utils.php_proto_rename(contents)
                with io.open(filename, 'w', encoding='UTF-8') as f:
                    f.write(contents)


class NodeJsProtoCopyTask(task_base.TaskBase):
    """Copies the .proto files into the gapic_code_dir/proto directory.
    """
    def execute(self, gapic_code_dir, src_proto_path, excluded_proto_path=[]):
        final_output_dir = os.path.join(gapic_code_dir, 'protos')
        for proto_path in src_proto_path:
            index = protoc_utils.find_google_dir_index(proto_path)
            for src_proto_file in protoc_utils.find_protos(
                    [proto_path], excluded_proto_path):
                relative_proto_file = src_proto_file[index:]
                dst_proto_file = os.path.join(
                    final_output_dir, relative_proto_file)
                dst_proto_dir = os.path.dirname(dst_proto_file)
                if not os.path.exists(dst_proto_dir):
                    self.exec_command(['mkdir', '-p', dst_proto_dir])
                self.exec_command(['cp', src_proto_file, dst_proto_file])
