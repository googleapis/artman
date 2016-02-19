gapi-pipeline
=============

Installation
------------

Install tox if it has not already been installed:

  ::
     $ sudo pip install tox  # done once, installed globally

Create, then activate the tox development environment:

  ::
     $ tox -e devenv
     $ . .tox/develop/bin/activate
     $(develop) ...

Once done developing, deactivate the development environment:

  ::
     $(develop) deactivate

Install packman:
  ::
     $ curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.30.2/install.sh | bash
     $ nvm install 5.0
     $ nvm use 5.0
     $ npm install -g googleapis-packman


Try it out
----------

To execute the pipeline locally, try the following example command:

::
    $ python execute_pipeline.py --pipeline_kwargs={\'sleep_secs\':2} SamplePipeline

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
       {'src_proto_path':
            ['test/testdata/gapi-example-library-proto/src/main/proto'],
        'import_proto_path':
            ['../gapi-core-proto/src/main/proto/'],
        'gapi_tools_path': '../gapi-tools',
        'service_yaml': ['test/testdata/gapi-example-library-proto/src/main/proto/google/example/library/library.yaml'],
        'veneer_yaml':
            ['test/testdata/gapi-example-library-proto/src/main/proto/google/example/library/library_veneer.yaml',
             'test/testdata/gapi-example-library-proto/src/main/proto/google/example/library/python_veneer.yaml'],
        'output_dir': 'test/output',
        'api_name': 'library',
        'vgen_output_dir': 'test/output/library'})" \
  PythonCodeGenPipeline

To run the Java pipeline (Note: This depends on the pubsub-beta branch
of googleapis/):

::
    $ python execute_pipeline.py \
        --config "../googleapis/pipeline_config/pipeline_core.yaml:core,pipeline_common.yaml:default" \
        JavaCorePipeline

    $ python execute_pipeline.py \
        --config "../googleapis/pipeline_config/pipeline_pubsub.yaml:pubsub_common|pubsub_java \
                  pipeline_common.yaml:default" \
        JavaGrpcClientPipeline

    $ python execute_pipeline.py \
        --config "../googleapis/pipeline_config/pipeline_pubsub.yaml:pubsub_common|pubsub_java, \
                  pipeline_common.yaml:default"  \
        JavaVkitClientPipeline

Running tests
-------------

To run tests and the linter, run this command:

::
    $ tox

Please always run this command before submitting changes.
