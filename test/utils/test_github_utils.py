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


import mock
import json
import pyfakefs.fake_filesystem as fake_fs
from pipeline.utils import github_utils
import stat

_USERNAME = 'fake_username'
_PASSWORD = 'fake_password'
_OWNER = 'fake-owner'
_REPO = 'fake-repo'
_BRANCH = 'fake-branch'
_MESSAGE = 'fake-message'
_BASE_URL = '{0}/repos/{1}/{2}/'.format(github_utils._API_URL, _OWNER, _REPO)
_POST_TREE_URL = _BASE_URL + 'git/trees'
_POST_COMMIT_URL = _BASE_URL + 'git/commits'
_GET_BRANCH_URL = _BASE_URL + 'branches/{0}'.format(_BRANCH)
_GET_TREE_URL = _BASE_URL + 'git/trees/'
_PATCH_REF_URL = _BASE_URL + 'git/refs/heads/{0}'.format(_BRANCH)
_EXPECTED_GET_ARGS = [mock.call(_GET_BRANCH_URL, data=None),
                      mock.call(_GET_TREE_URL + 'root_sha', data=None),
                      mock.call(_GET_TREE_URL + 'main_sha', data=None)]
_EXPECTED_POST_ARGS = [
    mock.call(_POST_TREE_URL,
              data=json.dumps({'tree':
                               [{'path': 'blank.txt',
                                 'mode': github_utils._FILE_MODE,
                                 'type': 'blob',
                                 'content': ''}]}, sort_keys=True),
              auth=(_USERNAME, _PASSWORD)),
    mock.call(_POST_TREE_URL,
              data=json.dumps({'base_tree': 'main_sha',
                               'tree':
                               [{'path': 'subdir',
                                 'mode': github_utils._TREE_MODE,
                                 'type': 'tree',
                                 'sha': 'subdir-tree-sha'},
                                {'path': 'hello.txt',
                                 'mode': github_utils._FILE_MODE,
                                 'type': 'blob',
                                 'content': 'hello local\n'}]}, sort_keys=True),
              auth=(_USERNAME, _PASSWORD)),
    mock.call(_POST_TREE_URL,
              data=json.dumps(
                  {'tree':
                   [{'path': 'executable.py',
                     'mode': github_utils._EXEC_MODE,
                     'type': 'blob',
                     'content': '#!/usr/bin/env python\n'}]}, sort_keys=True),
              auth=(_USERNAME, _PASSWORD)),
    mock.call(_POST_TREE_URL,
              data=json.dumps({'base_tree': 'root_sha',
                               'tree':
                               [{'path': 'main',
                                 'mode': github_utils._TREE_MODE,
                                 'type': 'tree',
                                 'sha': 'main-tree-sha'},
                                {'path': 'util',
                                 'mode': github_utils._TREE_MODE,
                                 'type': 'tree',
                                 'sha': 'util-tree-sha'}]}, sort_keys=True),
              auth=(_USERNAME, _PASSWORD)),
    mock.call(_POST_COMMIT_URL,
              data=json.dumps({'tree': 'root-tree-sha',
                               'parents': ['fake-commit-sha'],
                               'message': 'fake-message'}, sort_keys=True),
              auth=(_USERNAME, _PASSWORD))]
_EXPECTED_PATCH_ARGS = [
    mock.call(_PATCH_REF_URL,
              data=json.dumps({'sha': 'fake-commit-sha',
                               'force': True}, sort_keys=True),
              auth=(_USERNAME, _PASSWORD))]
_GET_SIDE_EFFECT = [
    mock.Mock(
        ok=True,
        content=json.dumps(
            {'sha': 'fake-branch-sha',
             'commit': {'commit': {'tree': {'sha': 'root_sha'}},
                        'sha': 'fake-commit-sha'}})),
    mock.Mock(ok=True,
              content=json.dumps(
                  {'sha': 'root_sha',
                   'tree': [{'path': 'main',
                             'mode': github_utils._TREE_MODE,
                             'sha': 'main_sha'}]}), sort_keys=True),
    mock.Mock(ok=True,
              content=json.dumps(
                  {'sha': 'main_sha',
                   'tree': [{'path': 'hello.txt',
                             'mode': github_utils._FILE_MODE,
                             'sha': 'hello.txt_sha'}]}, sort_keys=True))]
_POST_SIDE_EFFECT = [
    mock.Mock(ok=True,
              content=json.dumps({'sha': 'subdir-tree-sha'})),
    mock.Mock(ok=True,
              content=json.dumps({'sha': 'main-tree-sha'})),
    mock.Mock(ok=True,
              content=json.dumps({'sha': 'util-tree-sha'})),
    mock.Mock(ok=True,
              content=json.dumps({'sha': 'root-tree-sha'})),
    mock.Mock(ok=True,
              content=json.dumps({'sha': 'fake-commit-sha'}))]
_PATCH_RETURN_VAL = mock.Mock(ok=True, content=json.dumps({}))
fs = fake_fs.FakeFilesystem()
fs.CreateFile('/main/subdir/blank.txt')
fs.CreateFile('/main/hello.txt', contents='hello local\n')
# mark executable.py as an executable
fs.CreateFile('/util/executable.py', contents='#!/usr/bin/env python\n',
              st_mode=stat.S_IFREG | fake_fs.PERM_DEF_FILE | fake_fs.PERM_EXE)
os_module = fake_fs.FakeOsModule(fs)


@mock.patch.object(github_utils, 'open', side_effect=fake_fs.FakeFileOpen(fs))
@mock.patch('os.access', side_effect=os_module.access)
@mock.patch('os.path.isfile', side_effect=os_module.path.isfile)
@mock.patch('os.path.isdir', side_effect=os_module.path.isdir)
@mock.patch('os.listdir', side_effect=os_module.listdir)
@mock.patch('requests.patch', return_value=_PATCH_RETURN_VAL)
@mock.patch('requests.post', side_effect=_POST_SIDE_EFFECT)
@mock.patch('requests.get', side_effect=_GET_SIDE_EFFECT)
def test_github_utils_task(mock_get, mock_post, mock_patch, mock_listdir,
                           mock_isdir, mock_isfile, mock_access, mock_open):
    github_utils.push_dir_to_github('/', _USERNAME, _PASSWORD, _OWNER,
                                    _REPO, _BRANCH, _MESSAGE)
    mock_get.assert_has_calls(_EXPECTED_GET_ARGS)
    mock_post.assert_has_calls(_EXPECTED_POST_ARGS)
    mock_patch.assert_has_calls(_EXPECTED_PATCH_ARGS)
