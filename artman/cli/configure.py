# Copyright 2017 Google
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import
from collections import OrderedDict
import getpass
import importlib
import io
import json
import logging
import os

import six

from ruamel import yaml
import stringcase
import yaml

from artman.config.proto.user_config_pb2 import UserConfig, LocalConfig, GitHubConfig
from artman.utils.logger import logger
from artman.utils.logger import setup_logging
from google.protobuf.json_format import MessageToJson

__all__ = ('configure',)


def configure(log_level=logging.INFO):
    """Allow the user to write a new configuration file.

    Returns:
        int: An exit status.
    """
    user_config = UserConfig()

    # Walk the user through basic configuration.
    setup_logging(log_level)
    logger.info('Welcome to artman. We will get you configured.')
    logger.info('When this is done, config will be stored in ~/.artman/config.yaml.')
    logger.info('')

    # Go through each step.
    # These are split out to make testing them easier.
    user_config.local.CopyFrom(_configure_local_config())

    try:
        config_dir = os.path.expanduser('~/.artman/')
        os.makedirs(config_dir)
    except OSError:
        pass
    _write_pb_to_yaml(user_config, os.path.join(config_dir, 'config.yaml'))
    logger.success('Configuration written successfully to '
                   '~/.artman/config.yaml.')


def _configure_local_config():
    """Determine and return artman user local config.

    Returns:
        LocalConfig: The new artman local config settings.
    """
    answer = LocalConfig()

    # Ask the user for a local toolkit location.
    while not answer.toolkit:
        location = six.moves.input(
            'Where is your local toolkit repository? (If you do not have a '
            'toolkit repository, clone https://github.com/googleapis/toolkit/) '
            'Please provide an absolute path: ')
        if location:
            answer.toolkit = location

    # Done; return the answer.
    return answer


def _write_pb_to_yaml(pb, output):
    # Add yaml representer so that yaml dump can dump OrderedDict. The code
    # is coming from https://stackoverflow.com/questions/16782112.
    yaml.add_representer(OrderedDict, _represent_ordereddict)

    json_obj = _order_dict(json.loads(MessageToJson(pb)))
    with open(output, 'w') as outfile:
        yaml.dump(json_obj, outfile, default_flow_style=False)


def _represent_ordereddict(dumper, data):
    value = []
    for item_key, item_value in data.items():
        node_key = dumper.represent_data(item_key)
        node_value = dumper.represent_data(item_value)

        value.append((node_key, node_value))

    return yaml.nodes.MappingNode(u'tag:yaml.org,2002:map', value)


def _order_dict(od):
    # The whole key order is based on the simple name of the config field
    # instead of its full name (`username` vs `github.username`).
    keyorder = [
        'local', 'toolkit', 'github', 'username', 'token'
    ]
    res = OrderedDict()
    for k, v in sorted(od.items(), key=lambda i: keyorder.index(i[0])):
        if isinstance(v, dict):
            res[k] = _order_dict(v)
        elif isinstance(v, list):
            if isinstance(v[0], dict):
                result = []
                for d2 in v:
                    result.append(_order_dict(d2))
                res[k] = result
            else:
                res[k] = v
        else:
            res[k] = v
    return res
