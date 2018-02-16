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
import textwrap
import unittest

from google.protobuf import json_format
import mock
import pytest

from artman.config import loader
from artman.utils.logger import logger

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


class ReadUserConfigTests(unittest.TestCase):
    @mock.patch.object(logger, 'warn')
    def test_no_config(self, warn):
        loader.read_user_config('/unexisting_user_config.yaml')
        warn.assert_called_once_with(
            'No artman user config defined. Use the default one for this '
            'execution. Run `configure-artman` to set up user config.')

    @mock.patch.object(io, 'open')
    @mock.patch.object(os.path, 'isfile')
    def test_with_config(self, is_file, open_):
        # Create our stand-in config file.
        config_file = textwrap.dedent(u"""\
        local:
          toolkit: /toolkit
        """)
        is_file.return_value = True
        open_.return_value = io.StringIO(config_file)

        # Get the config and test the result.
        user_config = loader.read_user_config('~/.artman/config.yaml')
        assert user_config.local.toolkit == '/toolkit'
