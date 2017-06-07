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

"""Tasks related to Python gRPC code generation"""

import io
import os
import re
import tempfile
import time

from ruamel import yaml

from artman.utils import protoc_utils
from artman.tasks import task_base


class PythonChangePackageTask(task_base.TaskBase):
    """Copies source protos to a package that meets Python convention"""
    default_provides = ('final_src_proto_path',
                        'final_import_proto_path')

    _IDENTIFIER = '[A-Za-z_][A-Za-z_0-9]*'

    _BASE_PROTO_REGEX = (
        '(?P<prefix>{prefix})' +
        '(?P<package>' + _IDENTIFIER +
        '({separator}' + _IDENTIFIER + ')*{package_suffix})'
        '(?P<suffix>{suffix})')

    # E.g., `package google.foo.bar`
    _PACKAGE_REGEX = re.compile(_BASE_PROTO_REGEX.format(
        prefix='^package ',
        separator='\\.',
        package_suffix='',
        suffix=''))

    # E.g., `import "google/foo/bar";`
    _IMPORT_REGEX = re.compile(_BASE_PROTO_REGEX.format(
        prefix='^import "',
        separator='/',
        package_suffix='\\.proto',
        suffix='";'))

    # TODO (geigerj): add regex for documentation link updates?

    def execute(self, src_proto_path, import_proto_path, common_protos_yaml):
        with io.open(common_protos_yaml) as file_:
            common_protos_data = yaml.load(file_, Loader=yaml.Loader)

        # Treat google.protobuf, google.iam as a common proto package, even
        # though they are not included in the common-protos we generate.
        #
        # TODO (geigerj): remove 'google.iam' when it is included in the common
        # protos package.
        common_protos = ['google.protobuf', 'google.iam']
        for package in common_protos_data['packages']:
            common_protos.append('google.' + package['name'].replace('/', '.'))

        tmpdir = os.path.join(
            tempfile.gettempdir(), 'artman-python', str(int(time.time())))
        new_proto_dir = os.path.join(tmpdir, 'proto')
        new_src_path = set()
        new_import_path = [new_proto_dir]

        self._copy_and_transform_directories(
            src_proto_path, new_proto_dir, common_protos, paths=new_src_path)
        self._copy_and_transform_directories(
            import_proto_path, new_proto_dir, common_protos)

        # Update src_proto_path, import_proto_path
        return list(new_src_path), new_import_path

    def _extract_base_dirs(self, proto_file):
        """Return the proto file path derived from the package name."""

        with io.open(proto_file, 'rt', encoding='UTF-8') as proto:
            for line in proto:
                pkg = self._PACKAGE_REGEX.match(line)
                if pkg:
                    pkg = pkg.group('package')
                    return os.path.sep.join(pkg.split('.'))
            return ''

    def _transform(self, pkg, sep, common_protos):
        """Add 'proto' package after 'google' or 'google.cloud'

        Works with arbitrary separator (e.g., '/' for import statements,
        '.' for proto package statements, os.path.sep for filenames)
        """
        # Skip common protos
        pkg_list = pkg.split(sep)

        dotted = '.'.join(pkg_list)
        for common_pkg in common_protos:
            if dotted.startswith(common_pkg):
                return sep.join(pkg_list)

        if pkg_list[0] == 'google':
            if pkg_list[1] == 'cloud':
                return sep.join(['google', 'cloud', 'proto'] + pkg_list[2:])
            return sep.join(['google', 'cloud', 'proto'] + pkg_list[1:])
        return sep.join(pkg_list)

    def _copy_proto(self, src, dest, common_protos):
        """Copies a proto while fixing its imports"""
        with io.open(src, 'r', encoding='UTF-8') as src_lines:
            with io.open(dest, 'w+', encoding='UTF-8') as dest_file:
                for line in src_lines:
                    imprt = self._IMPORT_REGEX.match(line)
                    if imprt:
                        dest_file.write('import "{}";\n'.format(
                            self._transform(
                                imprt.group('package'), '/', common_protos)))
                    else:
                        dest_file.write(line)

    def _copy_and_transform_directories(
            self, src_directories, destination_directory, common_protos,
            paths=None):
        for path in src_directories:
            protos = list(protoc_utils.find_protos([path], []))
            for proto in protos:
                src_base_dirs = self._extract_base_dirs(proto)
                sub_new_src = os.path.join(
                    destination_directory,
                    self._transform(
                        src_base_dirs, os.path.sep, common_protos))
                if paths is not None:
                    paths.add(sub_new_src)

                dest = os.path.join(sub_new_src, os.path.basename(proto))
                if not os.path.exists(dest):
                    self.exec_command(['mkdir', '-p', sub_new_src])
                self._copy_proto(
                    proto, os.path.join(sub_new_src, dest), common_protos)
