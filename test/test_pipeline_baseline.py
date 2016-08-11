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
import pytest
import execute_pipeline


def get_expected_calls(baseline, binding, stderr=False):
    """Returns the list of expected calls of subprocess.check_output() and
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
            if stderr:
                commands.append(mock.call([
                    token.format(**binding) for token in tokens], stderr=-2))
            else:
                commands.append(mock.call([
                    token.format(**binding) for token in tokens]))
    return commands


def check_calls_match(expected_calls, actual_calls):
    err_str = 'Mismatch between expected and actual subprocess calls.\r\
        Expected: {}\rActual: {}'
    assert expected_calls == actual_calls, err_str.format(
        expected_calls, actual_calls)


def make_fake_python_output(output_dir):
    # Create an empty 'fake_output_api.py' in the output_dir. Do not invoke
    # 'touch' command with subprocess.call() because it's mocked.
    final_output_dir = os.path.join(output_dir, 'library-v1-gapic-gen-python')
    if not os.path.exists(final_output_dir):
        os.makedirs(final_output_dir)
    with open(os.path.join(final_output_dir, 'fake_output_api.py'), 'w'):
        pass


@mock.patch('pipeline.utils.task_utils.run_gradle_task')
@mock.patch('subprocess.call')
@mock.patch('subprocess.check_call')
@mock.patch('subprocess.check_output')
@mock.patch('os.chdir')
def _test_baseline(pipeline_name, config, pipeline_kwargs, baseline,
                   setup_output, mock_chdir, mock_check_output,
                   mock_check_call, mock_call, mock_gradle_task):
    reporoot = os.path.abspath('.')

    # Execute pipeline args
    args = ['--config', config, '--pipeline_kwargs', pipeline_kwargs,
            '--reporoot', reporoot, pipeline_name]

    # Mock output value of gradle tasks
    mock_gradle_task.return_value = 'MOCK_GRADLE_TASK_OUTPUT'
    mock_call.return_value = 0
    mock_check_output.return_value = ''

    # Output_dir as defined in artman yaml file
    output_dir = os.path.join(reporoot, 'test/testdata/test_output')

    # Run setup_output function
    if setup_output:
        setup_output(output_dir)

    # Run pipeline
    execute_pipeline.main(args)

    # Compare with the expected subprocess calls.
    expected_checked_calls = get_expected_calls(
        baseline, {'CWD': os.getcwd(), 'OUTPUT': output_dir}, True)
    check_calls_match(expected_checked_calls, mock_check_output.mock_calls)

    # Some tasks can use subprocess.call() instead of check_call(), they are
    # tracked separately.
    expected_subprocess_call = get_expected_calls(
        baseline + '.call', {'CWD': os.getcwd(), 'OUTPUT': output_dir})
    check_calls_match(expected_subprocess_call, mock_call.mock_calls)


python_pub_kwargs = {
        'repo_url': 'https://example-site.exampledomain.com/',
        'username': 'example-user',
        'password': 'example-pwd',
        'publish_env': 'dev'}


java_pub_kwargs = {
        'repo_url': 'http://maven.example.com/nexus/content/repositories/'
                    'releases',
        'username': 'example-maven-uname',
        'password': 'example-maven-pwd',
        'publish_env': 'prod'}


@pytest.mark.parametrize(
    'pipeline_name, language, extra_kwargs, baseline, setup_output',
    [
        ('GapicConfigPipeline', None, {}, 'config_pipeline', None),
        ('PythonGrpcClientPipeline', 'python', {},
         'python_grpc_client_nopub_pipeline', make_fake_python_output),
        ('PythonGrpcClientPipeline', 'python', python_pub_kwargs,
         'python_grpc_client_pub_pipeline', make_fake_python_output),
        ('PythonGapicClientPipeline', 'python', {},
         'python_gapic_client_pipeline', make_fake_python_output),
        ('JavaCoreProtoPipeline', 'java', {},
         'java_core_proto_nopub_pipeline', None),
        ('JavaCoreProtoPipeline', 'java', java_pub_kwargs,
         'java_core_proto_pub_pipeline', None),
        ('JavaGrpcClientPipeline', 'java', {},
         'java_grpc_client_nopub_pipeline', None),
        ('JavaGrpcClientPipeline', 'java', java_pub_kwargs,
         'java_grpc_client_pub_pipeline', None),
        ('JavaGapicClientPipeline', 'java', {},
         'java_gapic_client_pipeline', None),
        ('NodeJSGrpcClientPipeline', 'nodejs', {},
         'nodejs_grpc_client_pipeline', None),
        ('NodeJSGapicClientPipeline', 'nodejs', {},
         'nodejs_gapic_client_pipeline', None),
        ('RubyGrpcClientPipeline', 'ruby', {},
         'ruby_grpc_client_pipeline', None),
        ('RubyGapicClientPipeline', 'ruby', {},
         'ruby_gapic_client_pipeline', None),
        ('GoGrpcClientPipeline', 'go', {},
         'go_grpc_client_pipeline', None),
        ('GoGapicClientPipeline', 'go', {},
         'go_gapic_client_pipeline', None),
        ('PhpGrpcClientPipeline', 'php', {},
         'php_grpc_client_pipeline', None),
        ('PhpGapicClientPipeline', 'php', {},
         'php_gapic_client_pipeline', None),
        ('CSharpGrpcClientPipeline', 'csharp', {},
         'csharp_grpc_client_pipeline', None),
        ('CSharpGapicClientPipeline', 'csharp', {},
         'csharp_gapic_client_pipeline', None),
    ])
def test_generator(pipeline_name, language, extra_kwargs, baseline,
                   setup_output):
    artman_api_yaml = 'test/testdata/googleapis_test/gapic/api/' \
                      'artman_library.yaml:common'
    artman_language_yaml = 'test/testdata/googleapis_test/gapic/lang/' \
                           'common.yaml:default'
    if language is not None:
        artman_api_yaml += '|' + language
        artman_language_yaml += '|' + language

    config = ','.join([artman_api_yaml, artman_language_yaml])
    pipeline_kwargs = str(extra_kwargs)
    _test_baseline(pipeline_name, config, pipeline_kwargs, baseline,
                   setup_output)
