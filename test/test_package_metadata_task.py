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

import os
import pytest
import unittest
from ruamel import yaml

from artman.tasks import package_metadata_tasks


class PackageMetadataConfigTest(unittest.TestCase):
    # Print full diff when comparing actual/expected dict output
    maxDiff = None

    @pytest.fixture(autouse=True)
    def outdir(self, tmpdir):
        self.output_dir = tmpdir.mkdir('out')

    def test_package_metadata_config_gen_task(self):
        task = package_metadata_tasks.PackageMetadataConfigGenTask()
        repo_root = os.path.abspath('.')

        task.execute(
            api_name='fake',
            api_version='v1',
            language='python',
            root_dir='%s/googleapis' % repo_root,
            organization_name='google-cloud',
            output_dir=str(self.output_dir),
            proto_deps=['googleapis-common-protos'],
            artifact_type='GAPIC',
            src_proto_path=['path/to/protos'],
            release_level='beta'
        )
        actual_file = os.path.join(str(self.output_dir),
                                   'python_google-cloud-fake-v1_package2.yaml')
        expected_file = 'test/testdata/python_google-cloud-fake-v1_package2.yaml'
        with open(actual_file) as f:
            actual = yaml.safe_load(f)
        with open(expected_file) as f:
            expected = yaml.safe_load(f)
        # Don't compare files directly because yaml doesn't preserve ordering
        try:
            self.assertDictEqual(actual, expected)
        except:
            print("comparison failure: actual = " + actual_file + ", expected = " + expected_file)
            raise
