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
import subprocess
import yaml

import six

from pipeline.tasks import packman_tasks
from pipeline.tasks import task_base
from pipeline.tasks.requirements import grpc_requirements
from pipeline.utils import lang_params
from pipeline.utils import task_utils


class _SimpleProtoParams:
    def __init__(self, language):
        self.language = language
        self.path = None
        self.params = lang_params.LANG_PARAMS_MAP[language]

    def code_root(self, output_dir):
        return self.params.code_root(output_dir)

    def lang_out_param(self, output_dir, with_grpc):
        return '--{}_out={}'.format(self.language, self.code_root(output_dir))

    def grpc_plugin_path(self, dummy_toolkit_path):
        if self.path is None:
            self.path = subprocess.check_output(
                ['which', 'grpc_{}_plugin'.format(self.language)],
                stderr=subprocess.STDOUT)
            self.path = six.text_type(self.path)[:-1]
        return self.path

    def grpc_out_param(self, output_dir):
        return '--grpc_out=' + self.code_root(output_dir)

    @property
    def proto_compiler_command(self):
        return ['protoc']


class _JavaProtoParams:
    def __init__(self):
        self.path = None
        self.params = lang_params.LANG_PARAMS_MAP['java']

    def code_root(self, output_dir):
        return self.params.code_root(output_dir)

    def lang_out_param(self, output_dir, with_grpc):
        return '--java_out=' + self.code_root(output_dir)

    def grpc_plugin_path(self, toolkit_path):
        if self.path is None:
            print('start gradle process to locate GRPC Java plugin')
            self.path = task_utils.get_gradle_task_output(
                'showGrpcJavaPluginPath', toolkit_path)
        return self.path

    def grpc_out_param(self, output_dir):
        return '--grpc_out=' + self.code_root(output_dir)

    @property
    def proto_compiler_command(self):
        return ['protoc']


class _GoProtoParams:
    def __init__(self):
        self.path = None
        self.params = lang_params.LANG_PARAMS_MAP['go']

    def code_root(self, output_dir):
        return self.params.code_root(output_dir)

    def lang_out_param(self, output_dir, with_grpc):
        param = '--go_out='
        if with_grpc:
            param += 'plugins=grpc:'
        return param + self.code_root(output_dir)

    def grpc_plugin_path(self, toolkit_path):
        # Go gRPC code is generated through --go_out=plugin=grpc, no grpc
        # specific plugin.
        return None

    def grpc_out_param(self, output_dir):
        # Go gRPC output directory is specified from --go_out, thus this
        # returns None.
        return None

    @property
    def proto_compiler_command(self):
        return ['protoc']


class _PhpProtoParams:
    def __init__(self):
        self.path = None
        self.params = lang_params.LANG_PARAMS_MAP['php']

    def code_root(self, output_dir):
        return self.params.code_root(output_dir)

    def lang_out_param(self, output_dir, with_grpc):
        return '--php_out={}'.format(self.code_root(output_dir))

    def grpc_plugin_path(self, dummy_toolkit_path):
        if self.path is None:
            self.path = subprocess.check_output(
                ['which', 'protoc-gen-php'], stderr=subprocess.STDOUT)
            self.path = six.text_type(self.path)[:-1]
        return self.path

    def grpc_out_param(self, output_dir):
        return '--grpc_out=' + self.code_root(output_dir)

    @property
    def proto_compiler_command(self):
        return ['protoc']


class _RubyProtoParams:
    def __init__(self):
        self.path = None
        self.params = lang_params.LANG_PARAMS_MAP['ruby']

    def code_root(self, output_dir):
        return self.params.code_root(output_dir)

    def lang_out_param(self, output_dir, with_grpc):
        return '--ruby_out={}'.format(self.code_root(output_dir))

    def grpc_plugin_path(self, dummy_toolkit_path):
        # No plugin for grpc_toos_ruby_protoc
        return None

    def grpc_out_param(self, output_dir):
        return '--grpc_out=' + self.code_root(output_dir)

    @property
    def proto_compiler_command(self):
        return ['grpc_tools_ruby_protoc']


class _PythonProtoParams:
    def __init__(self):
        self.path = None
        self.params = lang_params.LANG_PARAMS_MAP['python']

    def code_root(self, output_dir):
        return self.params.code_root(output_dir)

    def lang_out_param(self, output_dir, with_grpc):
        return '--python_out={}'.format(self.code_root(output_dir))

    def grpc_plugin_path(self, dummy_toolkit_path):
        # No plugin for grpc.tools
        return None

    def grpc_out_param(self, output_dir):
        return '--grpc_python_out=' + self.code_root(output_dir)

    @property
    def proto_compiler_command(self):
        return ['python', '-m', 'grpc.tools.protoc']


_PROTO_PARAMS_MAP = {
    'ruby': _RubyProtoParams(),
    'java': _JavaProtoParams(),
    'go': _GoProtoParams(),
    'csharp': _SimpleProtoParams('csharp'),
    'php': _PhpProtoParams(),
    'python': _PythonProtoParams()
}


def _find_protobuf_path(toolkit_path):
    """Fetch and locate protobuf source"""
    print('Searching for latest protobuf source')
    return task_utils.get_gradle_task_output(
        'showProtobufPath', toolkit_path)


def _group_by_dirname(protos):
    """Groups the file paths by direct parent directory.

    Returns:
        A dict mapping from the directory name to the list of proto files in
        it.
    """
    dirs = {}
    for proto in protos:
        dirname = os.path.dirname(proto)
        if dirname not in dirs:
            dirs[dirname] = [proto]
        else:
            dirs[dirname].append(proto)
    return dirs


def _protoc_header_params(proto_path,
                          toolkit_path):
    proto_path = proto_path[:]
    proto_path.append(_find_protobuf_path(toolkit_path))
    return (['--proto_path=' + path for path in proto_path])


def _protoc_desc_params(output_dir, desc_out_file):
    return (['--include_imports',
             '--include_source_info',
             '-o', os.path.join(output_dir, desc_out_file)])


def _protoc_proto_params(proto_params, pkg_dir, with_grpc):
    return [proto_params.lang_out_param(pkg_dir, with_grpc)]


def _protoc_grpc_params(proto_params, pkg_dir, toolkit_path):
    params = []
    plugin_param = proto_params.grpc_plugin_path(toolkit_path)
    if plugin_param:
        params.append('--plugin=protoc-gen-grpc={}'.format(plugin_param))
    grpc_param = proto_params.grpc_out_param(pkg_dir)
    if grpc_param:
        params.append(grpc_param)
    return params


def _pkg_root_dir(output_dir, api_name, api_version, organization_name,
                  language):
    api_full_name = task_utils.api_full_name(
        api_name, api_version, organization_name)
    return os.path.join(output_dir, api_full_name + '-gen-' + language)


def _prepare_pkg_dir(output_dir, api_name, api_version, organization_name,
                     language):
    proto_params = _PROTO_PARAMS_MAP[language]
    pkg_dir = _pkg_root_dir(
        output_dir, api_name, api_version, organization_name, language)
    subprocess.check_output([
        'mkdir', '-p', proto_params.code_root(pkg_dir)],
        stderr=subprocess.STDOUT)
    return pkg_dir


class ProtoDescGenTask(task_base.TaskBase):
    """Generates proto descriptor set"""
    default_provides = 'descriptor_set'

    def execute(self, src_proto_path, import_proto_path, output_dir,
                api_name, api_version, organization_name, toolkit_path,
                desc_proto_path=None):
        desc_proto_path = desc_proto_path or []
        desc_protos = list(
            task_utils.find_protos(src_proto_path + desc_proto_path))
        header_proto_path = import_proto_path + desc_proto_path
        header_proto_path.extend(src_proto_path)
        desc_out_file = task_utils.api_full_name(
            api_name, api_version, organization_name) + '.desc'
        print('Compiling descriptors for {0}'.format(desc_protos))
        self.exec_command(['mkdir', '-p', output_dir])
        # DescGen don't use _group_by_dirname right now because
        #   - it doesn't have to
        #   - and multiple invocation will overwrite the desc_out_file
        self.exec_command(
            ['protoc'] +
            _protoc_header_params(header_proto_path, toolkit_path) +
            _protoc_desc_params(output_dir, desc_out_file) +
            desc_protos)
        return os.path.join(output_dir, desc_out_file)

    def validate(self):
        return [grpc_requirements.GrpcRequirements]


class ProtocCodeGenTaskBase(task_base.TaskBase):
    default_provides = 'intermediate_package_dir'

    def _execute_proto_codegen(
            self, language, src_proto_path, import_proto_path,
            output_dir, api_name, api_version, organization_name,
            toolkit_path, gen_proto=False, gen_grpc=False,
            final_src_proto_path=None, final_import_proto_path=None):
        src_proto_path = final_src_proto_path or src_proto_path
        import_proto_path = final_import_proto_path or import_proto_path
        proto_params = _PROTO_PARAMS_MAP[language]
        pkg_dir = _prepare_pkg_dir(
            output_dir, api_name, api_version, organization_name, language)

        if gen_proto:
            protoc_proto_params = _protoc_proto_params(
                proto_params, pkg_dir, with_grpc=True)
        else:
            protoc_proto_params = []

        if gen_grpc:
            protoc_grpc_params = _protoc_grpc_params(
                proto_params, pkg_dir, toolkit_path)
        else:
            protoc_grpc_params = []

        # protoc-gen-go must compile all protos in a package at the same
        # time, and *only* the protos in that package. This doesn't break
        # other languages, so we do it that way for all of them.
        for (dirname, protos) in _group_by_dirname(
                task_utils.find_protos(src_proto_path)).items():
            self.exec_command(
                proto_params.proto_compiler_command +
                _protoc_header_params(
                    import_proto_path + src_proto_path, toolkit_path) +
                protoc_proto_params +
                protoc_grpc_params +
                protos)

        return pkg_dir


class ProtoCodeGenTask(ProtocCodeGenTaskBase):
    """Generates protos"""
    def execute(self, language, src_proto_path, import_proto_path,
                output_dir, api_name, api_version, organization_name,
                toolkit_path, final_src_proto_path=None,
                final_import_proto_path=None):
        return self._execute_proto_codegen(
            language, src_proto_path, import_proto_path, output_dir,
            api_name, api_version, organization_name, toolkit_path,
            gen_proto=True, final_src_proto_path=final_src_proto_path,
            final_import_proto_path=final_import_proto_path)

    def validate(self):
        return [grpc_requirements.GrpcRequirements]


class GrpcCodeGenTask(ProtocCodeGenTaskBase):
    """Generates the gRPC client library"""
    def execute(self, language, src_proto_path, import_proto_path,
                toolkit_path, output_dir, api_name, api_version,
                organization_name, final_src_proto_path=None,
                final_import_proto_path=None):
        return self._execute_proto_codegen(
            language, src_proto_path, import_proto_path, output_dir,
            api_name, api_version,  organization_name, toolkit_path,
            gen_grpc=True, final_src_proto_path=final_src_proto_path,
            final_import_proto_path=final_import_proto_path)

    def validate(self):
        return [grpc_requirements.GrpcRequirements]


class ProtoAndGrpcCodeGenTask(ProtocCodeGenTaskBase):
    """Generates protos and the gRPC client library"""
    def execute(self, language, src_proto_path, import_proto_path,
                toolkit_path, output_dir, api_name, api_version,
                organization_name, final_src_proto_path=None,
                final_import_proto_path=None):
        return self._execute_proto_codegen(
            language, src_proto_path, import_proto_path, output_dir,
            api_name, api_version, organization_name, toolkit_path,
            gen_proto=True, gen_grpc=True,
            final_src_proto_path=final_src_proto_path,
            final_import_proto_path=final_import_proto_path)

    def validate(self):
        return [grpc_requirements.GrpcRequirements]


class GoLangUpdateImportsTask(task_base.TaskBase):
    """Modifies the import in the generated pb.go files and copies them into
    the final_repo_dir.

    The Go compiler requires source files to specify the import path as the
    relative path from $GOPATH/src, however the import paths to other proto
    packages in the generated pb.go files don't fullfill this requirement. This
    task finds such import lines and rewrites them in the form of the original
    code.
    """

    def execute(self, api_name, api_version, organization_name, language,
                go_import_base, output_dir, final_repo_dir):
        pkg_dir = _prepare_pkg_dir(output_dir, api_name, api_version,
                                   organization_name, language)
        print(pkg_dir)
        for pbfile in self.find_pb_files(pkg_dir):
            out_file = os.path.join(final_repo_dir, 'proto',
                                    os.path.relpath(pbfile, pkg_dir))
            print('outfile {}'.format(out_file))
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
                packman_flags=None, repo_dir=None, final_src_proto_path=None,
                final_import_proto_path=None):
        src_proto_path = final_src_proto_path or src_proto_path
        import_proto_path = final_import_proto_path or import_proto_path

        packman_flags = packman_flags or []
        api_name_arg = task_utils.packman_api_name(
            task_utils.api_full_name(api_name, api_version, organization_name))
        pkg_dir = _pkg_root_dir(
            output_dir, api_name, api_version, organization_name, language)
        arg_list = [language, api_name_arg, '-o', pkg_dir,
                    '--package_prefix', 'grpc-']

        # Import path must be absolute. See
        #   https://github.com/googleapis/packman/issues/1
        import_proto_path = [os.path.abspath(imp) for imp in import_proto_path]

        arg_list += [arg for imp in import_proto_path for arg in ('-i', imp)]
        arg_list += [arg for src in src_proto_path for arg in ('-r', src)]
        arg_list += packman_flags
        if repo_dir:
            arg_list += ['-r', repo_dir]
        self.run_packman(*arg_list)
        return os.path.join(pkg_dir, language)


class JavaGrpcPackmanTask(GrpcPackmanTask):

    def execute(self, language, api_name, api_version, organization_name,
                output_dir, src_proto_path, import_proto_path, gapic_api_yaml,
                packman_flags=None, repo_dir=None, proto_deps=None):
        proto_deps = proto_deps or []
        packman_flags = packman_flags or []
        if len(packman_flags) == 0:
            packman_flags.append('--experimental_alt_java')
            for dep in proto_deps:
                packman_flags.append('--proto_gen_pkg_dep')
                packman_flags.append(dep)
            if len(gapic_api_yaml) > 0:
                gapic_yaml = os.path.abspath(gapic_api_yaml[0])
                packman_flags += ['--gapic_yaml', gapic_yaml]
        return super(JavaGrpcPackmanTask, self).execute(
            language, api_name, api_version, organization_name, output_dir,
            src_proto_path, import_proto_path, packman_flags=packman_flags,
            repo_dir=repo_dir)


class RubyGrpcCopyTask(task_base.TaskBase):
    """Copies the generated protos and gRPC client library to
    the final_repo_dir/lib.
    """
    def execute(self, api_name, api_version, language, organization_name,
                output_dir, final_repo_dir):
        pkg_dir = _pkg_root_dir(
            output_dir, api_name, api_version, organization_name, language)
        final_output_dir = os.path.join(final_repo_dir, 'lib')
        print('Copying %s/* to %s.' % (pkg_dir, final_output_dir))
        if not os.path.exists(final_output_dir):
            self.exec_command(['mkdir', '-p', final_output_dir])
        for entry in sorted(os.listdir(pkg_dir)):
            src_path = os.path.join(pkg_dir, entry)
            self.exec_command([
                'cp', '-rf', src_path, final_output_dir])


class GoExtractImportBaseTask(task_base.TaskBase):
    default_provides = 'go_import_base'

    def execute(self, gapic_api_yaml):
        for yaml_file in gapic_api_yaml:
            if not os.path.exists(yaml_file):
                continue
            with open(yaml_file) as f:
                gapic_config = yaml.load(f)
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
