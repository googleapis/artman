import collections
import difflib
import os
import re
import subprocess
import time
import unittest2

# Set os PATH to use our fake executables. This must be done before project-
# specific imports to cause module-level global variables to be initialized
# correctly.
os.environ['PATH'] = 'test/fake-bin:' + os.environ['PATH']

from pipeline.pipelines import pipeline_factory
from taskflow import engines


def check_diff(test_name, testdata_dir, actual, to_ignore=()):
    """Find baseline file for test and diff against actual results, ignoring any
    sequences matching any regex in `to_ignore`"""
    actual_str = ''
    for filename in actual:
        actual_str += (
            '============== file: {} ==============\n'.format(filename))
        contents = actual[filename]
        for ignore in to_ignore:
            contents = re.sub(ignore, '[...]', contents)
        actual_str += contents
    filename = os.path.join(testdata_dir, test_name + '.baseline')
    with open(filename, 'r') as baseline_file:
        baseline_str = baseline_file.read()
    return difflib.context_diff(
        actual_str.split('\n'), baseline_str.split('\n'),
        fromfile='test output', tofile=filename)


def compile_output(output_dir):
    """Find output and compile dictionary sorted on filename"""
    output_lst = []
    for root, dirs, files in os.walk(output_dir):
        for filename in files:
            full_name = os.path.join(root, filename)
            with open(full_name, 'r') as this_file:
                contents = this_file.read()
            output_lst.append(
                (os.path.relpath(full_name, output_dir), contents))
    return collections.OrderedDict(sorted(output_lst, key=lambda x: x[0]))


class TestPipelineBaseline(unittest2.TestCase):

    def test_python_baseline(self):

        # Used to locate the .baseline file
        test_name = 'python_pipeline'

        # The real output location of running the pipeline
        output_dir = '/var/tmp/pipeline-baseline-test'

        # Pipeline kwargs
        kwargs_ = {
            'service_proto_path':
                ['test/testdata/gapi-example-library-proto/src/main/proto'],
            'import_proto_path':
                ['test/fake-repos/gapi-core-proto/src/main/proto/'],
            'gapi_tools_path': 'test/fake-repos/gapi-tools',
            'service_yaml': [
                'test/testdata/gapi-example-library-proto/src/main/proto/google/'
                'example/library/library.yaml'],
            'veneer_yaml': [
                'test/testdata/gapi-example-library-proto/src/main/proto/google/'
                    'example/library/library_veneer.yaml',
                'test/testdata/gapi-example-library-proto/src/main/proto/google/'
                    'example/library/python_veneer.yaml'],
            'output_dir': output_dir}

        # Sequences to sanitize from the actual output, here, the location of
        # this repo, which is user-specific
        to_ignore = (subprocess.check_output(['pwd'])[:-1],)

        subprocess.call(['rm', '-rf', output_dir])

        # Run pipeline
        pipeline = pipeline_factory.make_pipeline(
            'PythonCodeGenPipeline', **kwargs_)
        engine = engines.load(pipeline.flow, engine='serial')
        engine.run()

        output = compile_output(output_dir)

        # Diff against baseline file
        diff = list(
            check_diff(test_name, 'test/testdata', output, to_ignore=to_ignore))
        msg = 'Test output located at: {0}\n\n{1}'.format(
            output_dir, '\n'.join(diff))
        self.assertEquals(len(diff), 0, msg=msg)
