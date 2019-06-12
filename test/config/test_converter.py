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

import io
import os
import unittest
import yaml

from artman.config import converter
from artman.config import loader


class ConverterTest(unittest.TestCase):
    TESTDATA = os.path.join(
        os.path.realpath(os.path.dirname(__file__)), 'testdata')

    def test_pubsub_java(self):
        self._test('artman_pubsub.yaml', 'java_gapic',
                   'expected_pubsub_java_legacy_config.yaml')

    def test_pubsub_java_proto(self):
        self._test('artman_pubsub.yaml', 'java_proto',
                   'expected_pubsub_java_proto_legacy_config.yaml')

    def test_pubsub_python(self):
        self._test('artman_pubsub.yaml', 'python_gapic',
                   'expected_pubsub_python_legacy_config.yaml')

    def test_library(self):
        self._test('artman_library.yaml', 'java_gapic',
                   'expected_library_config.yaml')

    def _test(self, artman_yaml, artifact_name, expected_legacy_config):
        artifact_config = loader.load_artifact_config(os.path.join(
            self.TESTDATA, artman_yaml), artifact_name)
        actual_legacy_config_dict = converter.convert_to_legacy_config_dict(
            artifact_config, '/tmp/input', '/tmp/output')
        with io.open(os.path.join(
                self.TESTDATA, expected_legacy_config), 'r') as yaml_file:
            expected_legacy_config_dict = yaml.load(yaml_file)
            self.assertDictEqual(
                expected_legacy_config_dict, actual_legacy_config_dict,
                'Actual yaml is:\n{}\nExpected yaml is:\n{}\n'.format(
                    yaml.dump(actual_legacy_config_dict, default_flow_style=False),
                    yaml.dump(expected_legacy_config_dict, default_flow_style=False)))


if __name__ == '__main__':
    unittest.main()
