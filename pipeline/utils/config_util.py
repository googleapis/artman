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


"""Utils related to config files"""


import yaml


def load_config_spec(config_spec, config_sections, repl_vars, language):
    config_split = config_spec.strip().split(':')
    config_path = config_split[0]
    if len(config_split) > 1:
        config_sections = config_split[1].split('|')
    data = {}
    with open(config_path) as config_file:
        all_config_data = yaml.load(config_file)
    for section in config_sections:
        data.update(all_config_data[section])
    if language in all_config_data:
        data.update(all_config_data[language])

    var_replace_config_data(data, repl_vars)
    return data


def var_replace_config_data(data, repl_vars):
    for (k, v) in data.items():
        if type(v) is list:
            data[k] = [var_replace(lv, repl_vars) for lv in v]
        elif type(v) is not bool:
            data[k] = var_replace(v, repl_vars)


def var_replace(in_str, repl_vars):
    new_str = in_str
    for (k, v) in repl_vars.items():
        new_str = new_str.replace('${' + k + '}', v)
    return new_str
