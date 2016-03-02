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

To run the Python pipeline for logging:

::
    $ python execute_pipeline.py \
        --config "../googleapis/pipeline_config/pipeline_logging.yaml\
        :logging_common|logging_python,\
        pipeline_common.yaml:default" \
        PythonGrpcClientPipeline

    $ python execute_pipeline.py \
        --config "../googleapis/pipeline_config/pipeline_logging.yaml\
        :logging_common|logging_python,\
        pipeline_common.yaml:default" \
        PythonVkitClientPipeline

To run the Java pipeline:

::
    $ python execute_pipeline.py \
        --config "../googleapis/pipeline_config/pipeline_core.yaml:core,\
        pipeline_common.yaml:default" \
        JavaCorePipeline

    $ python execute_pipeline.py \
        --config "../googleapis/pipeline_config/pipeline_pubsub.yaml:pubsub_common|pubsub_java,\
                  pipeline_common.yaml:default" \
        JavaGrpcClientPipeline

    $ python execute_pipeline.py \
        --config "../googleapis/pipeline_config/pipeline_pubsub.yaml:pubsub_common|pubsub_java,\
        pipeline_common.yaml:default" \
        JavaVkitClientPipeline

To run the Go pipeline, first the core protos have to be compiled into the output directory.
Note: this won't be necessary once a public repository for core proto pb.go files.

::
    $ python execute_pipeline.py \
       --config "../googleapis/pipeline_config/pipeline_core.yaml:core,\
       ../googleapis/pipeline_config/pipeline_logging.yaml:logging_go,\
       pipeline_common.yaml:default" \
       GoCoreProtoPipeline

The actual Go pipeline is as follows:

::
    $ python execute_pipeline.py \
       --config "../googleapis/pipeline_config/pipeline_logging.yaml:logging_common|logging_go|logging_type,\
       pipeline_common.yaml:default" \
       GoCoreProtoPipeline

    $ python execute_pipeline.py \
       --config "../googleapis/pipeline_config/pipeline_logging.yaml:logging_common|logging_go,\
       pipeline_common.yaml:default" \
       GoGrpcClientPipeline

    $ python execute_pipeline.py \
       --config "../googleapis/pipeline_config/pipeline_logging.yaml:logging_common|logging_go,\
       pipeline_common.yaml:default" \
       GoVkitClientPipeline

Running tests
-------------

To run tests and the linter, run this command:

::
    $ tox

Please always run this command before submitting changes.
