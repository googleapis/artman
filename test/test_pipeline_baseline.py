import mock
import os
import tempfile
import unittest2

from pipeline.pipelines import pipeline_factory
from taskflow import engines


def get_expected_calls(baseline, binding):
    """Returns the list of expected subprocess calls.

    The expected commandlines are listed in the baseline files located
    under test/testdata, with placeholders of {OUTPUT} for the output dir and
    {CWD} for the current working directory. Those values are supplied from
    binding parameter.
    """
    commands = []
    with open(os.path.join('test', 'testdata', baseline + '.baseline')) as f:
        for line in f:
            tokens = line.strip().split()
            commands.append(mock.call([
                token.format(**binding) for token in tokens]))
    return commands


class TestPipelineBaseline(unittest2.TestCase):

    @mock.patch('subprocess.call')
    def _test_python_baseline(self, task_name, test_name, mock_call):

        # The real output location of running the pipeline
        output_dir = tempfile.mkdtemp(suffix=test_name)

        # Pipeline kwargs
        kwargs_ = {
            'src_proto_path':
                ['test/testdata/gapi-example-library-proto/src/main/proto'],
            'import_proto_path':
                ['test/fake-repos/gapi-core-proto/src/main/proto/'],
            'gapi_tools_path': 'test/fake-repos/gapi-tools',
            'service_yaml': [
                'test/testdata/gapi-example-library-proto/src/main/proto/'
                'google/example/library/library.yaml'],
            'veneer_yaml': [
                'test/testdata/gapi-example-library-proto/src/main/proto/'
                    'google/example/library/library_veneer.yaml',
                'test/testdata/gapi-example-library-proto/src/main/proto/'
                    'google/example/library/python_veneer.yaml'],
            'output_dir': output_dir,
            'api_name': 'library-v1',
            'vgen_output_dir': output_dir}

        # Create an empty 'fake_output_api.py' in the output_dir. Do not invoke
        #  'touch' command with subprocess.call() because it's mocked.
        with open(os.path.join(output_dir, 'fake_output_api.py'), 'w'):
            pass

        # Run pipeline
        pipeline = pipeline_factory.make_pipeline(
            task_name, **kwargs_)
        engine = engines.load(pipeline.flow, engine='serial')
        engine.run()

        # Compare with the expected subprocess calls.
        mock_call.assert_has_calls(get_expected_calls(
            test_name, {'CWD': os.getcwd(), 'OUTPUT': output_dir}))

    def test_python_grpc_client_baseline(self):
        self._test_python_baseline('PythonGrpcClientPipeline',
                                   'python_grpc_client_pipeline')

    def test_python_vkit_client_baseline(self):
        self._test_python_baseline('PythonVkitClientPipeline',
                                   'python_vkit_client_pipeline')
