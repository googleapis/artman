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
import unittest

from google.protobuf import json_format
import pytest

from artman.config import loader

CUR_DIR = os.path.dirname(os.path.realpath(__file__))

class ArtmanYamlParserTest(unittest.TestCase):
    def testValidArtmanYaml(self):
        artman_yaml = os.path.join(CUR_DIR, 'testdata/valid_artman.yaml')
        loader._parse(artman_yaml)

    def testInvalidArtmanYaml(self):
        artman_yaml = os.path.join(CUR_DIR, 'testdata/invalid_artman.yaml')
        with pytest.raises(json_format.ParseError) as excinfo:
            loader._parse(artman_yaml)
        expected = '"googleapis.artman.Config" has no field named "a".'
        assert expected in str(excinfo.value)

    def testValidArtmanYamlNotFound(self):
        artman_yaml = 'does_no_exist.yaml'
        with pytest.raises(ValueError) as excinfo:
            loader._parse(artman_yaml)
        expected = loader.CONFIG_NOT_FOUND_ERROR_MESSAGE_FORMAT % artman_yaml
        assert expected == str(excinfo.value)
