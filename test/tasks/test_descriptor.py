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

from __future__ import absolute_import
import unittest
import pypandoc
import mock
import restructuredtext_lint

from artman.tasks import descriptor_set_tasks
from google.protobuf import descriptor_pb2 as desc


class PythonDocsConversionTests(unittest.TestCase):
    @mock.patch.object(pypandoc, 'convert_text')
    def test_execute(self, convert_text):
        convert_text.return_value = ''
        descriptor_set = 'test/tasks/data/test_descriptor/descriptor_set'
        task = descriptor_set_tasks.PythonDocsConvertionTask()
        task.execute(descriptor_set)
        convert_text.assert_called()

    @unittest.expectedFailure
    def test_valid_rst(self):
        descriptor_set = 'test/tasks/data/test_descriptor/descriptor_set'
        task = descriptor_set_tasks.PythonDocsConvertionTask()
        updated_descriptor = task.execute(descriptor_set)

        desc_set = desc.FileDescriptorSet()
        with open(updated_descriptor, 'rb') as f:
            desc_set.ParseFromString(f.read())

        lint_errors = []
        comment_count = 0
        for comment in gather_comments_from_descriptor_set(desc_set):
            lint_errors.extend(restructuredtext_lint.lint(comment))
            comment_count += 1

        print(lint_errors)
        assert len(lint_errors) == 0
        assert comment_count == 1913

    def test_proto_link_re(self):
        valid_tests = [
            ["[Foo][bar.Foo]", [("Foo", "bar.Foo")]],
            ["[Foo][]", [("Foo", "")]],
            [
                "test [Foo][bar.Foo] fuzz [Baz][fob.Baz] bunk",
                [("Foo", "bar.Foo"), ("Baz", "fob.Baz")]
            ]
        ]
        invalid_tests = [
            "[][Foo]",
            "[Foo](baz)"
        ]
        self._test_pattern(descriptor_set_tasks._proto_link_re,
                           valid_tests, invalid_tests)

    def test_relative_link_re(self):
        valid_tests = [
            ["[Foo](/foo/bar)", [("Foo", "/foo/bar")]],
            [
                "test [Foo](/foo/bar) fuzz [Baz](/fob/baz) bunk",
                [("Foo", "/foo/bar"), ("Baz", "/fob/baz")]
            ]
        ]
        invalid_tests = [
            "[link]()",
            "[](foo)",
            "[Foo](foo/bar)",
            "[link](https://foo)",
        ]
        self._test_pattern(descriptor_set_tasks._relative_link_re,
                           valid_tests, invalid_tests)

    @classmethod
    def _test_pattern(cls, pattern, valid_tests, invalid_tests):
        for comment, expected_matches in valid_tests:
            actual_matches = pattern.findall(comment)
            assert(len(actual_matches) == len(expected_matches))
            for exp, act in zip(expected_matches, actual_matches):
                assert exp == act[1:], 'exp={}, act={}'.format(exp, act[1:])

        for comment in invalid_tests:
            matches = pattern.findall(comment)
            assert not matches, 'unexpected matches: {}'.format(matches)

    @classmethod
    def setUpClass(cls):
        pypandoc.pandoc_download.download_pandoc(version='1.19.2')


def gather_comments_from_descriptor_set(desc_set):
    for file_descriptor_proto in desc_set.file:
        if not file_descriptor_proto.source_code_info:
            continue

        for location in file_descriptor_proto.source_code_info.location:
            yield location.leading_comments
            yield location.leading_comments
            for comment in location.leading_detached_comments:
                yield comment
