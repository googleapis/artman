gapi-pipeline
=============

Installation
------------

Install tox if it has not already been installed:

  ::
     $ sudo pip install tox  # done once, installed globally

Create, then activate the tox development environment:

  ::
     $ tox -e py27
     $ . .tox/develop/bin/activate
     $(develop) ...

Once done developing, deactivate the development environment:

  ::
     $(develop) deactivate


Try it out
----------

To execute the pipeline locally, try the following example command:

   $python execute_pipeline.py --pipeline_kwargs={\'sleep_secs\':2} SamplePipeline

To execute with pipeline remotely, start two consoles and run the following command
in one console:

::
    $ python start_conductor.py


And then run the following command for multiple times with different parameter:

::
    $ python execute_pipeline.py --pipeline_kwargs={\'sleep_secs\':2} --remote_mode SamplePipeline


Please note, there is no guarantee that your pipeline job will be claimed by the
conductor running on your machine. It can also be picked up by other conductor
processes. You can run the second command for multiple times, and chances are
good that your conductor will pick up one job at least.

To run the Python pipeline:

::
    $ python execute_pipeline.py \
       --pipeline_kwargs="(
       {'service_proto_path':
            ['test/testdata/gapi-example-library-proto/src/main/proto'],
        'import_proto_path':
            ['../gapi-core-proto/src/main/proto/'],
        'gapi_tools_path': '../gapi-tools',
        'service_yaml': ['test/testdata/gapi-example-library-proto/src/main/proto/google/example/library/library.yaml'],
        'veneer_yaml':
            ['test/testdata/gapi-example-library-proto/src/main/proto/google/example/library/library_veneer.yaml',
             'test/testdata/gapi-example-library-proto/src/main/proto/google/example/library/python_veneer.yaml'],
        'output_dir': 'test/output'})" \
  PythonCodeGenPipeline
