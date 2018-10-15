# Copyright 2018 Google Inc. All Rights Reserved.
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

"""Tasks that work directly with a descriptor set"""

import os
import re

import pypandoc
from artman.tasks import task_base

from google.protobuf import descriptor_pb2 as desc


class PythonDocsConvertionTask(task_base.TaskBase):
    """Converts proto comments to restructuredtext format.

    Proto comments are expected to be in markdown format, and to possibly
    contain links to other protobuf types and relative URLs that will not
    resolve to correct documentation using standard tools.

    This task performs the following transformations on the documentation
    in the descriptor set:
    - Replace proto links with literals (e.g. [Foo][bar.baz.Foo] -> `Foo`)
    - Resolve relative URLs to https://cloud.google.com
    - Run pandoc to convert from markdown to restructuredtext"""
    default_provides = 'descriptor_set'

    def execute(self, descriptor_set):
        desc_set = desc.FileDescriptorSet()
        with open(descriptor_set, 'rb') as f:
            desc_set.ParseFromString(f.read())

        for file_descriptor_proto in desc_set.file:
            if not file_descriptor_proto.source_code_info:
                continue

            for location in file_descriptor_proto.source_code_info.location:
                location.leading_comments = md2rst(location.leading_comments)
                location.trailing_comments = md2rst(location.trailing_comments)
                detached = [md2rst(c) for c in location.leading_detached_comments]
                del location.leading_detached_comments[:]
                location.leading_detached_comments.extend(detached)

        desc_file, desc_ext = os.path.splitext(descriptor_set)
        new_descriptor_set = desc_file + '_updated_py_docs' + desc_ext

        with open(new_descriptor_set, mode='wb') as f:
            f.write(desc_set.SerializeToString())

        return new_descriptor_set


_proto_link_re = re.compile(
    r'(\[(?P<text>[^\]]+)\]\[(?P<uri>[A-Za-z_][A-Za-z_.0-9]*)?\])')
_relative_link_re = re.compile(
    r'(\[(?P<text>[^\]]+)\]\((?P<uri>/[^\)]+)\))')
_new_lines = re.compile(r'(?P<newlines>(\r?\n)+)(?P<followup>[^\r\n])')


def _replace(comment, pattern, repl_fn):
    index = 0
    strs = []
    for m in pattern.finditer(comment):
        strs.append(comment[index:m.start()])
        strs.append(repl_fn(m))
        index = m.end()
    strs.append(comment[index:])
    return ''.join(strs)


def _replace_proto_link(comment):
    def _format(m):
        return "`{}`".format(m.group('text'))
    return _replace(comment, _proto_link_re, _format)


def _replace_relative_link(comment):
    def _format(m):
        return "[{}](https://cloud.google.com{})".format(m.group('text'),
                                                         m.group('uri'))
    return _replace(comment, _relative_link_re, _format)


def _insert_spaces(comment):
    def _format(m):
        return "{} {}".format(m.group('newlines'), m.group('followup'))
    # After replacement, add a leading space
    return " " + _replace(comment, _new_lines, _format)


def _add_space(comment):
    def _format(m):
        return "[{}](https://cloud.google.com{})".format(m.group('text'),
                                                         m.group('uri'))
    return _replace(comment, _relative_link_re, _format)


def md2rst(comment):
    """Convert a comment from protobuf markdown to restructuredtext.

    This method:
    - Replaces proto links with literals (e.g. [Foo][bar.baz.Foo] -> `Foo`)
    - Resolves relative URLs to https://cloud.google.com
    - Runs pandoc to convert from markdown to restructuredtext
    """
    comment = _replace_proto_link(comment)
    comment = _replace_relative_link(comment)
    # Calling pypandoc.convert_text is slow, so we try to avoid it if there are
    # no special characters in the markdown.
    if any([i in comment for i in '`[]*_']):
        comment = pypandoc.convert_text(comment, 'rst', format='md')
        # Comments are now valid restructuredtext, but there is a problem. They
        # are being inserted back into a descriptor set, and there is an
        # expectation that each line of a comment will begin with a space, to
        # separate it from the '//' that begins the comment. You would think
        # that we could ignore this detail, but it will cause formatting
        # problems down the line in gapic-generator because parsing code will
        # try to remove the leading space, affecting the indentation of lines
        # that actually do begin with a space, so we insert the additional
        # space now. Comments that are not processed by pypandoc will already
        # have a leading space, so should not be changed.
        comment = _insert_spaces(comment)
    return comment


_DESC_TASK_DICT = {
    'python': PythonDocsConvertionTask,
}


class EmptyDescriptorTask(task_base.EmptyTask):
    """An empty descriptor task.

     The taskflow library will produce a duplicate task error if multiple
     EmptyTask instances are added to a pipeline, so we create a unique
     subclass."""
    pass


def get_descriptor_set_task(language):
    return _DESC_TASK_DICT.get(language, EmptyDescriptorTask)
