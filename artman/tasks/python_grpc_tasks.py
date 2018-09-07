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

    def execute(self, src_proto_path, import_proto_path,
                organization_name):
        self._organization_name = organization_name

        # Treat google.protobuf, google.iam as a common proto package, even
        # though they are not included in the common-protos we generate.
        #
        # TODO (geigerj): remove 'google.iam' when it is included in the common
        # protos package.
        common_protos = [
            'google.protobuf',
            'google.iam',
            'google.api',
            'google.longrunning',
            'google.rpc',
            'google.type',
            'google.logging.type',
        ]

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
        """Transform to the appropriate proto package layout.

        Works with arbitrary separator (e.g., '/' for import statements,
        '.' for proto package statements, os.path.sep for filenames)
        """
        if sep != '.' and pkg.endswith('.proto'):
            dotted = pkg[:-6].replace(sep, '.')
            suffix = '.proto'
        else:
            dotted = pkg.replace(sep, '.')
            suffix = ''

        # Sanity check: Do not transform common protos.
        for common_pkg in common_protos:
            if dotted.startswith(common_pkg):
                return pkg

        # Special case: If the organization name is "google-cloud", then we
        # have to ensure that "cloud" exists in the path. The protos
        # themselves may not follow this.
        if 'cloud' not in dotted and self._organization_name == 'google-cloud':
            dotted = dotted.replace('google.', 'google.cloud.', 1)

        # Transform into the ideal proto path.
        # What essentially should happen here is that "{api}.{vN}" should
        # change to "{api}_{vN}".
        dotted = re.sub(r'\.v([\da-z_]*)([\d]+)\b', r'_v\1\2.proto', dotted)

        # Edge case: Some internal customers use "vNalpha" and "vNbeta".
        # Rather than make the regular expression more complicated, catch
        # this as a one-off.
        if re.search(r'\.v[\d]+alpha\b', dotted):
            dotted = re.sub(r'\.v([\d]+)alpha\b', r'_v\1alpha.proto', dotted)
        if re.search(r'\.v[\d]+beta\b', dotted):
            dotted = re.sub(r'\.v([\d]+)beta\b', r'_v\1beta.proto', dotted)
        if re.search(r'\.v[\d]+eap\b', dotted):
            dotted = re.sub(r'\.v([\d]+)eap\b', r'_v\1eap.proto', dotted)

        # Done; return with the appropriate separator.
        return dotted.replace('.', sep) + suffix

    def _copy_proto(self, src, dest, common_protos):
        """Copies a proto while fixing its imports"""
        with io.open(src, 'r', encoding='UTF-8') as src_lines:
            with io.open(dest, 'w+', encoding='UTF-8') as dest_file:
                for line in src_lines:
                    import_ = self._IMPORT_REGEX.match(line)
                    if import_:
                        dest_file.write('import "{}";\n'.format(
                            self._transform(
                                import_.group('package'), '/', common_protos)))
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


class PythonMoveProtosTask(task_base.TaskBase):
    default_provides = {'grpc_code_dir'}

    def execute(self, grpc_code_dir, gapic_code_dir):
        """Move the protos into the GAPIC structure.

        This copies the ``x/y/z/proto/`` directory over to be a sibling
        of ``x/y/z/gapic/`` in the GAPIC code directory. In the event of
        an inconsistency on the prefix, the GAPIC wins.

        Args:
            grpc_code_dir (str): The location where the GRPC code was
                generated.
            gapic_code_dir (str): The location where the GAPIC code was
                generated.
        """
        # Determine the appropriate source and target directory.
        # We can get this by drilling in to the GAPIC artifact until we get to
        # a "gapic" directory.
        src = self._get_subdir_path(grpc_code_dir, 'proto')
        target = self._get_subdir_path(
            os.path.join(gapic_code_dir, 'google'),
            'gapic',
        )

        # Move the contents into the GAPIC directory.
        self.exec_command(['mv', os.path.join(src, 'proto'), target])

        # Create an __init__.py file in the proto directory.
        # This is necessary for Python 2.7 compatibility.
        self.exec_command([
            'touch', os.path.join(target, 'proto', '__init__.py'),
        ])

        # Remove the grpc directory.
        self.exec_command(['rm', '-rf', grpc_code_dir])

        # Clear out the grpc_code_dir, so future tasks perceive it as
        # not being a thing anymore.
        return {'grpc_code_dir': None}

    def _get_subdir_path(self, haystack, needle):
        """Return the subpath which contains the ``needle`` directory.

        Args:
            haystack (str): The top-level directory in which the subdirectory
                should appear.
            needle (str): The directory being sought.

        Returns:
            str: The path, relative to ``haystack``, where the subdirectory
                was found.

        Raises:
            RuntimeError: If the subdirectory is not found.
        """
        for path, dirs, files in os.walk(haystack):
            if needle in dirs:
                return path
        raise RuntimeError('Path %s not found in %s.' % (needle, haystack))
