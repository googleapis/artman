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

from __future__ import print_function
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


def format_arg(arg, bindings):
    for (k, v) in bindings.items():
        arg = arg.replace(v, '{' + k + '}')
    return arg


def format_args(args, bindings):
    return ' '.join([format_arg(arg, bindings) for arg in args])


def format_calls(calls, bindings):
    return '\n'.join([format_args(args, bindings)
                      for (name, (args,), kwargs) in calls])


def check_calls_match(baseline_file, expected_calls, actual_calls, bindings):
    mismatch_text = 'Mismatch between expected and actual subprocess calls.\n'

    def format_err(exp, act):
        return (mismatch_text + 'Baseline file: ' + baseline_file +
                '.baseline\n' + 'Expected:\n' + exp + '\nActual:\n' + act)
    exp = format_calls(expected_calls, bindings)
    act = format_calls(actual_calls, bindings)
    assert exp == act, format_err(exp, act)


def _test_error(pipeline_name, language, config, pipeline_kwargs,
                expected_error):
    reporoot = os.path.abspath('.')

    # Execute pipeline args
    args = ['--config', config,
            '--pipeline_kwargs', pipeline_kwargs,
            '--reporoot', reporoot,
            pipeline_name]
    if language:
        args += ['--language', language]

    # Run pipeline
    with pytest.raises(expected_error):
        execute_pipeline.main(args)


@mock.patch('pipeline.utils.task_utils.get_gradle_task_output')
@mock.patch('pipeline.tasks.package_metadata_tasks.'
            'PackageMetadataConfigGenTask._write_yaml')
@mock.patch('pipeline.tasks.python_grpc_tasks.PythonChangePackageTask.execute')
@mock.patch('subprocess.call')
@mock.patch('subprocess.check_call')
@mock.patch('subprocess.check_output')
@mock.patch('time.time')
@mock.patch('os.chdir')
def _test_baseline(pipeline_name, config, extra_args, baseline,
                   mock_chdir, mock_time, mock_check_output, mock_check_call,
                   mock_call, mock_python_pkg_task, mock__write_yaml,
                   mock_gradle_task):
    reporoot = os.path.abspath('.')

    # Execute pipeline args
    args = ['--config', config,
            '--reporoot', reporoot,
            pipeline_name] + extra_args

    # Mock output value of tasks
    mock_gradle_task.return_value = 'MOCK_GRADLE_TASK_OUTPUT'
    mock_python_pkg_task.return_value = (
        ['PYTHON_PKG_PROTOS1', 'PYTHON_PKG_PROTOS2'], 'PYTHON_GOOGLEAPIS')

    mock_call.return_value = 0
    mock_check_output.return_value = ''

    # Output_dir as defined in artman yaml file
    output_dir = os.path.join(reporoot, 'test/testdata/test_output')

    # Run pipeline
    print('executing with args: %r.' % (args,))
    execute_pipeline.main(args)

    bindings = {'CWD': reporoot, 'OUTPUT': output_dir}

    # Compare with the expected subprocess calls.
    expected_checked_calls = get_expected_calls(
        baseline, bindings, True)
    check_calls_match(baseline, expected_checked_calls,
                      mock_check_output.mock_calls, bindings)

    # Some tasks can use subprocess.call() instead of check_call(), they are
    # tracked separately.
    expected_subprocess_call = get_expected_calls(
        baseline + '.call', bindings)
    check_calls_match(baseline, expected_subprocess_call, mock_call.mock_calls,
                      bindings)


python_pub_extra_args = ['--pipeline_kwargs', str({
        'repo_url': 'https://example-site.exampledomain.com/',
        'username': 'example-user',
        'password': 'example-pwd',
        'publish_env': 'dev'})]


java_pub_extra_args = ['--pipeline_kwargs', str({
        'repo_url': 'http://maven.example.com/nexus/content/repositories/'
                    'releases',
        'username': 'example-maven-uname',
        'password': 'example-maven-pwd',
        'publish_env': 'prod'})]


@pytest.mark.parametrize(
    'pipeline_name, language, extra_kwargs, expected_error',
    [
        ('GrpcClientPipeline', None, {}, ValueError),
        ('GrpcClientPipeline', '', {}, ValueError),
        ('GrpcClientPipeline', 'cylon', {}, ValueError)
    ])
def test_generator_errors(pipeline_name, language, extra_kwargs,
                          expected_error):
    artman_api_yaml = 'test/testdata/googleapis_test/gapic/api/' \
                      'artman_library.yaml'
    artman_language_yaml = 'test/testdata/googleapis_test/gapic/lang/' \
                           'common.yaml'
    config = ','.join([artman_api_yaml, artman_language_yaml])

    pipeline_kwargs = str(extra_kwargs)
    _test_error(pipeline_name, language, config, pipeline_kwargs,
                expected_error)


@pytest.mark.parametrize(
    'pipeline_name, language, extra_args, baseline',
    [
        ('GapicConfigPipeline', None, [], 'config_pipeline'),
        ('GrpcClientPipeline', 'python', [],
         'python_grpc_client_nopub_pipeline'),
        ('GrpcClientPipeline', 'python', python_pub_extra_args,
         'python_grpc_client_pub_pipeline'),
        ('GapicClientPipeline', 'python', [],
         'python_gapic_client_pipeline'),
        ('GrpcClientPipeline', 'java', [],
         'java_grpc_client_nopub_pipeline'),
        ('GrpcClientPipeline', 'java', java_pub_extra_args,
         'java_grpc_client_pub_pipeline'),
        ('GapicClientPipeline', 'java', [],
         'java_gapic_client_pipeline'),
        ('GrpcClientPipeline', 'nodejs', [],
         'nodejs_grpc_client_pipeline'),
        ('GapicClientPipeline', 'nodejs', [],
         'nodejs_gapic_client_pipeline'),
        ('GrpcClientPipeline', 'ruby', [],
         'ruby_grpc_client_pipeline'),
        ('GapicClientPipeline', 'ruby', [],
         'ruby_gapic_client_pipeline'),
        ('GrpcClientPipeline', 'go', [],
         'go_grpc_client_pipeline'),
        ('GapicClientPipeline', 'go', [],
         'go_gapic_client_pipeline'),
        ('GrpcClientPipeline', 'php', [],
         'php_grpc_client_pipeline'),
        ('GapicClientPipeline', 'php', [],
         'php_gapic_client_pipeline'),
        # Use PHP to test stage_output flag in GapicClientPipeline
        ('GapicClientPipeline', 'php', ['--stage_output'],
         'php_gapic_client_stage_pipeline'),
        ('GrpcClientPipeline', 'csharp', [],
         'csharp_grpc_client_pipeline'),
        ('GapicClientPipeline', 'csharp', [],
         'csharp_gapic_client_pipeline'),
    ])
def test_generator(pipeline_name, language, extra_args, baseline):
    artman_api_yaml = 'test/testdata/googleapis_test/gapic/api/' \
                      'artman_library.yaml'
    artman_language_yaml = 'test/testdata/googleapis_test/gapic/lang/' \
                           'common.yaml'
    config = ','.join([artman_api_yaml, artman_language_yaml])
    if language:
        extra_args += ['--language', language]
    _test_baseline(pipeline_name, config, extra_args, baseline)


@pytest.mark.parametrize(
    'extra_args, baseline',
    [
        ([], 'gapic_batch_pipeline'),
        (['--stage_output'], 'gapic_batch_staging_pipeline')
    ]
)
def test_generator_batch(extra_args, baseline):
    config = 'test/testdata/googleapis_test/gapic/batch/staging.yaml'
    pipeline_name = 'GapicClientBatchPipeline'
    _test_baseline(pipeline_name,
                   config,
                   extra_args,
                   baseline)
