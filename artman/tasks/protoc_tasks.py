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

import os
import re
from ruamel import yaml

import six

from artman.tasks import packman_tasks
from artman.tasks import task_base
from artman.tasks.requirements import grpc_requirements
from artman.utils import task_utils
from artman.utils.logger import logger
from artman.utils import protoc_utils


class ProtoDescGenTask(task_base.TaskBase):
    """Generates proto descriptor set"""
    default_provides = 'descriptor_set'

    def execute(self, src_proto_path, import_proto_path, output_dir,
                api_name, api_version, organization_name, toolkit_path,
                desc_proto_path=None, excluded_proto_path=[]):
        desc_proto_path = desc_proto_path or []
        desc_protos = list(
            protoc_utils.find_protos(src_proto_path + desc_proto_path,
                                     excluded_proto_path))
        header_proto_path = import_proto_path + desc_proto_path
        header_proto_path.extend(src_proto_path)
        desc_out_file = task_utils.api_full_name(
            api_name, api_version, organization_name) + '.desc'
        logger.info('Compiling descriptors for {0}'.format(desc_protos))
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

    def validate(self):
        return [grpc_requirements.GrpcRequirements]


class ProtocCodeGenTaskBase(task_base.TaskBase):
    """Generates protos"""
    def _execute_proto_codegen(
            self, language, src_proto_path, import_proto_path,
            pkg_dir, api_name, api_version, organization_name,
            toolkit_path, gapic_api_yaml, gen_proto=False, gen_grpc=False,
            final_src_proto_path=None, final_import_proto_path=None,
            excluded_proto_path=[]):
        gapic_api_yaml = gapic_api_yaml[0] if gapic_api_yaml else None
        src_proto_path = final_src_proto_path or src_proto_path
        import_proto_path = final_import_proto_path or import_proto_path
        proto_params = protoc_utils.PROTO_PARAMS_MAP[language]

        if gen_proto:
            protoc_proto_params = protoc_utils.protoc_proto_params(
                proto_params, pkg_dir, gapic_api_yaml, with_grpc=True)
        else:
            protoc_proto_params = []

        if gen_grpc:
            protoc_grpc_params = protoc_utils.protoc_grpc_params(
                proto_params, pkg_dir, toolkit_path)
        else:
            protoc_grpc_params = []

        # protoc-gen-go must compile all protos in a package at the same
        # time, and *only* the protos in that package. This doesn't break
        # other languages, so we do it that way for all of them.
        for (dirname, protos) in protoc_utils.group_by_dirname(
                protoc_utils.find_protos(src_proto_path, excluded_proto_path)).items():
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
                toolkit_path, gapic_api_yaml, final_src_proto_path=None,
                final_import_proto_path=None, excluded_proto_path=[]):
        pkg_dir = protoc_utils.prepare_proto_pkg_dir(
            output_dir, api_name, api_version, organization_name, language)
        return self._execute_proto_codegen(
            language, src_proto_path, import_proto_path, pkg_dir,
            api_name, api_version, organization_name, toolkit_path,
            gapic_api_yaml, gen_proto=True,
            final_src_proto_path=final_src_proto_path,
            final_import_proto_path=final_import_proto_path,
            excluded_proto_path=excluded_proto_path)

    def validate(self):
        return [grpc_requirements.GrpcRequirements]


class GrpcCodeGenTask(ProtocCodeGenTaskBase):
    default_provides = 'grpc_code_dir'

    """Generates the gRPC client library"""
    def execute(self, language, src_proto_path, import_proto_path,
                toolkit_path, output_dir, api_name, api_version,
                organization_name, gapic_api_yaml, final_src_proto_path=None,
                final_import_proto_path=None, excluded_proto_path=[]):
        pkg_dir = protoc_utils.prepare_grpc_pkg_dir(
            output_dir, api_name, api_version, organization_name, language)
        return self._execute_proto_codegen(
            language, src_proto_path, import_proto_path, pkg_dir,
            api_name, api_version,  organization_name, toolkit_path,
            gapic_api_yaml, gen_grpc=True,
            final_src_proto_path=final_src_proto_path,
            final_import_proto_path=final_import_proto_path,
            excluded_proto_path=excluded_proto_path)

    def validate(self):
        return [grpc_requirements.GrpcRequirements]


class ProtoAndGrpcCodeGenTask(ProtocCodeGenTaskBase):
    default_provides = 'grpc_code_dir'

    """Generates protos and the gRPC client library"""
    def execute(self, language, src_proto_path, import_proto_path,
                toolkit_path, output_dir, api_name, api_version,
                organization_name, gapic_api_yaml, final_src_proto_path=None,
                final_import_proto_path=None, excluded_proto_path=[]):
        pkg_dir = protoc_utils.prepare_grpc_pkg_dir(
            output_dir, api_name, api_version, organization_name, language)
        return self._execute_proto_codegen(
            language, src_proto_path, import_proto_path, pkg_dir,
            api_name, api_version, organization_name, toolkit_path,
            gapic_api_yaml, gen_proto=True, gen_grpc=True,
            final_src_proto_path=final_src_proto_path,
            final_import_proto_path=final_import_proto_path,
            excluded_proto_path=excluded_proto_path)

    def validate(self):
        return [grpc_requirements.GrpcRequirements]


class GoLangUpdateImportsTask(task_base.TaskBase):
    """Modifies the import in the generated pb.go files and copies them into
    the gapic_code_dir.

    The Go compiler requires source files to specify the import path as the
    relative path from $GOPATH/src, however the import paths to other proto
    packages in the generated pb.go files don't fullfill this requirement. This
    task finds such import lines and rewrites them in the form of the original
    code.
    """

    def execute(self, api_name, api_version, organization_name, language,
                go_import_base, output_dir, gapic_code_dir):
        pkg_dir = protoc_utils.prepare_grpc_pkg_dir(output_dir, api_name, api_version,
                                                    organization_name, language)
        logger.info(pkg_dir)
        for pbfile in self.find_pb_files(pkg_dir):
            out_file = os.path.join(gapic_code_dir, 'proto',
                                    os.path.relpath(pbfile, pkg_dir))
            logger.info('outfile {}'.format(out_file))
            out_dir = os.path.dirname(out_file)
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)
            with open(pbfile) as fin:
                with open(out_file, 'w') as fout:
                    for line in fin:
                        fout.write(self.modify_imports(go_import_base, line))

    def find_pb_files(self, dirname):
        for root, _, files in os.walk(dirname):
            for filename in files:
                # os.path.splitext splits "foo.pb.go" to ("foo.pb", "go").
                (base, ext) = os.path.splitext(filename)
                if ext == '.go' and os.path.splitext(base)[1] == '.pb':
                    yield os.path.join(root, filename)

    def modify_imports(self, go_import_base, line):
        """Modifies incorrect imports in a pb.go file to point the correct
        files."""
        pattern = r'^import ([a-zA-Z0-9_]* )?"google/'
        replacement = 'import \g<1>"%s/proto/google/' % go_import_base
        return re.sub(pattern, replacement, line)


class GrpcPackmanTask(packman_tasks.PackmanTaskBase):
    default_provides = 'package_dir'

    def execute(self, language, api_name, api_version, organization_name,
                output_dir, src_proto_path, import_proto_path,
                packman_flags=None, remote_repo_dir=None,
                final_src_proto_path=None, final_import_proto_path=None):
        src_proto_path = final_src_proto_path or src_proto_path
        import_proto_path = final_import_proto_path or import_proto_path

        packman_flags = packman_flags or []
        api_name_arg = task_utils.packman_api_name(
            task_utils.api_full_name(api_name, api_version, organization_name))
        pkg_dir = protoc_utils.pkg_root_dir(
            output_dir, api_name, api_version, organization_name, language)
        arg_list = [language, api_name_arg, '-o', pkg_dir,
                    '--package_prefix', 'grpc-']

        # Import path must be absolute. See
        #   https://github.com/googleapis/packman/issues/1
        import_proto_path = [os.path.abspath(imp) for imp in import_proto_path]

        arg_list += [arg for imp in import_proto_path for arg in ('-i', imp)]
        arg_list += [arg for src in src_proto_path for arg in ('-r', src)]
        arg_list += packman_flags
        if remote_repo_dir:
            arg_list += ['-r', remote_repo_dir]
        self.run_packman(*arg_list)
        return os.path.join(pkg_dir, language)


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


class GoExtractImportBaseTask(task_base.TaskBase):
    default_provides = 'go_import_base'

    def execute(self, gapic_api_yaml):
        for yaml_file in gapic_api_yaml:
            if not os.path.exists(yaml_file):
                continue
            with open(yaml_file) as f:
                gapic_config = yaml.load(f, Loader=yaml.Loader)
            if not gapic_config:
                continue
            language_settings = gapic_config.get('language_settings')
            if not language_settings:
                continue
            go_settings = language_settings.get('go')
            if not go_settings:
                continue
            if 'package_name' in go_settings:
                return go_settings.get('package_name')


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
