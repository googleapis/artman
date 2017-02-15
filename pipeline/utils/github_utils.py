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

"""Utility functions related to GitHub interaction. Uses the GitHub API with
reference https://developer.github.com/v3/"""

from __future__ import absolute_import
import requests
import json
import os

from six.moves import urllib

_API_URL = 'https://api.github.com'
# modes for git objects
_FILE_MODE = u'100644'
_EXEC_MODE = u'100755'
_TREE_MODE = u'040000'


def _get_immediate_subdirs(a_dir):
    return [dir_item for dir_item in os.listdir(a_dir)
            if (os.path.isdir(os.path.join(a_dir, dir_item)))]


def _get_immediate_files(a_dir):
    return [dir_item for dir_item in os.listdir(a_dir)
            if os.path.isfile(os.path.join(a_dir, dir_item))]


def _exec_request(http_method, url, req_data=None, username=None,
                  password=None):
    """Make an HTTP request with given data and (username, password) tuple.

    Returns:
        json response to request

    Raises:
        HTTPError: HTTP Request failed
    """
    if username and password:
        attempt = http_method(url, data=req_data, auth=(username, password))
    else:
        attempt = http_method(url, data=req_data)
    if attempt.ok:
        return json.loads(attempt.content)
    else:
        raise urllib.error.HTTPError(url, attempt.status_code, attempt.content,
                                     attempt.headers, None)


def _get_file_mode(el):
    if os.path.isfile(el) and os.access(el, os.X_OK):
        return _EXEC_MODE
    return _FILE_MODE


def _get_subtree_sha(orig_tree, path):
    gen = (x for x in orig_tree['tree'] if (x['path'] == path and
                                            x['mode'] == _TREE_MODE))
    subtree_item = next(gen, None)
    if subtree_item:
        return subtree_item['sha']


# TODO: Have this function also upload symlinks to the repository
# according to GitHub protocol
def _extend_git_tree(curr_dir, username, password, base_url,
                     orig_tree_sha=None):
    """Create a git tree from contents of local directory curr_dir.

    If orig_tree_sha is provided, the new tree inherits all structure from
    the remote tree with sha orig_tree_sha. The new tree will always include
    files or paths that are present in the remote tree. However, if the
    curr_dir and the remote tree  have conflicting contents for files with the
    same path, the new tree will use the content of curr_dir.

    Returns:
        New tree object as a dictionary, if curr_dir had files
        Otherwise, returns None

    Raises:
        HTTPError: An HTTP request used to construct the tree failed
    """
    if orig_tree_sha:
        orig_tree = _exec_request(
            requests.get, base_url + 'git/trees/{0}'.format(orig_tree_sha))
    tree_els = []
    for subdir in _get_immediate_subdirs(curr_dir):
        subtree_sha = None
        if orig_tree_sha:
            subtree_sha = _get_subtree_sha(orig_tree, subdir)
        subtree = _extend_git_tree(os.path.join(curr_dir, subdir), username,
                                   password, base_url, subtree_sha)
        # Add the subtree to tree_els iff subdir contains files
        if subtree:
            tree_els.append({'path': subdir, 'mode': _TREE_MODE,
                             'type': 'tree', 'sha': subtree['sha']})
    for exec_or_file in _get_immediate_files(curr_dir):
        with open(os.path.join(curr_dir, exec_or_file), 'r') as f:
            path_content = f.read()
        tree_els.append({'path': exec_or_file,
                         'mode': _get_file_mode(os.path.join(curr_dir,
                                                             exec_or_file)),
                         'type': 'blob', 'content': path_content})
    # Git doesn't allow empty trees
    if tree_els:
        data_dict = {'tree': tree_els}
        if orig_tree_sha:
            data_dict['base_tree'] = orig_tree_sha
        return _exec_request(requests.post, base_url + 'git/trees',
                             json.dumps(data_dict, sort_keys=True),
                             username, password)


def push_dir_to_github(local_dir, username, password, owner, repo, branch,
                       message='Automated commit from artman'):
    """Push all content in local_dir to the given GitHub repo branch.

    The effect of running the task is not exactly the same as that of a
    forced git push: this won't change or delete files that are missing
    in the local repo but are present in the remote repo.

    Returns:
        None

    Raises:
        ValueError: local_dir was empty
        HTTPError: An HTTP request used to construct the Git tree failed
    """
    base_url = '{0}/repos/{1}/{2}/'.format(_API_URL, owner, repo)
    # get the sha of the latest commit on this branch
    branch_item = _exec_request(
        requests.get,
        base_url + 'branches/{0}'.format(branch))
    commit_sha = branch_item['commit']['sha']
    orig_tree_sha = branch_item['commit']['commit']['tree']['sha']
    root_tree = _extend_git_tree(local_dir, username, password,
                                 base_url, orig_tree_sha)
    if not root_tree:
        raise ValueError('Cannot push empty folder {0}'.format(local_dir))
    # make a new commit using the built tree, with the previous commit as its
    # only parent
    req_data = json.dumps({
        'message': message,
        'parents': [commit_sha],
        'tree': root_tree['sha'],
    }, sort_keys=True)
    new_commit_item = _exec_request(requests.post,
                                    base_url + 'git/commits', req_data,
                                    username, password)
    # update the repository's refs so that the branch head is the new commit
    _exec_request(requests.patch,
                  base_url + 'git/refs/heads/{0}'.format(branch),
                  json.dumps({'sha': new_commit_item['sha'],
                              'force': True}, sort_keys=True),
                  username, password)
