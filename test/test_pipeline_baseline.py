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
import os

from pipeline.pipelines import pipeline_factory
from taskflow import engines


def get_expected_calls(baseline, binding):
    """Returns the list of expected calls of subprocess.check_call() and
    subprocess.call().

    The expected commandlines are listed in the baseline files located
    under test/testdata, with placeholders of {OUTPUT} for the output dir and
    {CWD} for the current working directory. Those values are supplied from
    binding parameter.
    """
    commands = []
    filename = os.path.join('test', 'testdata', baseline + '.baseline')
    if not os.path.exists(filename):
        return commands
    with open(filename) as f:
        for line in f:
            tokens = line.strip().split()
            commands.append(mock.call([
                token.format(**binding) for token in tokens]))
    return commands


@mock.patch('pipeline.utils.task_utils.runGradleTask')
@mock.patch('subprocess.call')
@mock.patch('subprocess.check_call')
def _test_baseline(task_name, test_name, language, output_dir, mock_check_call,
                   mock_call, mock_gradle_task):
    # Pipeline kwargs
    kwargs_ = {
        'src_proto_path': ['test/fake-repos/fake-proto'],
        'import_proto_path':
            ['test/fake-repos/gapi-core-proto/src/main/proto/'],
        'gapi_tools_path': 'test/fake-repos/gapi-tools',
        'service_yaml': [
            'test/testdata/gapi-example-library-proto/src/main/proto/'
            'google/example/library/library.yaml'],
        'veneer_language_yaml': [
            'test/testdata/gapi-example-library-proto/src/main/proto/'
                'google/example/library/' + language + '_veneer.yaml'],
        'veneer_api_yaml': [
            'test/testdata/gapi-example-library-proto/src/main/proto/'
                'google/example/library/library_veneer.yaml'],
        'output_dir': output_dir,
        'api_name': 'library-v1',
        'auto_merge': True,
        'auto_resolve': True,
        'ignore_base': False,
        'final_repo_dir': output_dir}

    # Mock output value of gradle tasks
    mock_gradle_task.return_value = 'MOCK_GRADLE_TASK_OUTPUT'
    mock_call.return_value = 0

    # Run pipeline
    pipeline = pipeline_factory.make_pipeline(task_name, **kwargs_)
    engine = engines.load(pipeline.flow, engine='serial')
    engine.run()

    # Compare with the expected subprocess calls.
    mock_check_call.assert_has_calls(get_expected_calls(
        test_name, {'CWD': os.getcwd(), 'OUTPUT': output_dir}))

    # Some tasks can use subprocess.call() instead of check_call(), they are
    # tracked separately.
    expected_subprocess_call = get_expected_calls(
        test_name + '.call', {'CWD': os.getcwd(), 'OUTPUT': output_dir})
    if expected_subprocess_call:
        mock_call.assert_has_calls(expected_subprocess_call)


def _test_python_baseline(task_name, test_name, tmpdir):
    output_dir = str(tmpdir)

    # Create an empty 'fake_output_api.py' in the output_dir. Do not invoke
    #  'touch' command with subprocess.call() because it's mocked.
    final_output_dir = os.path.join(output_dir, 'library-v1-veneer-gen-python')
    if not os.path.exists(final_output_dir):
        os.makedirs(final_output_dir)
    with open(os.path.join(final_output_dir, 'fake_output_api.py'), 'w'):
        pass

    _test_baseline(task_name, test_name, 'python', output_dir)


def test_python_grpc_client_baseline(tmpdir):
    _test_python_baseline('PythonGrpcClientPipeline',
                          'python_grpc_client_pipeline',
                          tmpdir)


def test_python_vkit_client_baseline(tmpdir):
    _test_python_baseline('PythonVkitClientPipeline',
                          'python_vkit_client_pipeline',
                          tmpdir)


def _test_go_baseline(task_name, test_name, tmpdir):
    _test_baseline(task_name, test_name, 'go', str(tmpdir))


def test_go_grpc_client_baseline(tmpdir):
    _test_go_baseline('GoGrpcClientPipeline', 'go_grpc_client_pipeline',
                      tmpdir)


def test_go_vkit_client_baseline(tmpdir):
    _test_go_baseline('GoVkitClientPipeline', 'go_vkit_client_pipeline',
                      tmpdir)
