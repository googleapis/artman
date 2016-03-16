Google API Artifact Manager
===========================

Google API Artifact manager (artman) is a set of modules used to automate the
creation of software artifacts related to APIS defined using `protobuf`_ IDL.

artman is an extensible framework that is responsible for creating all artifacts
related to an API including

- distribution packages in all supported programming languages
- generic documentation websites
- language-specific documentation websites (javadoc, readthedocs, etc)

from the protobuf source IDL and additional configuration in yaml files.

.. _`protobuf`: https://github.com/google/protobuf


Installation
------------

*N.B., at the moment, this library is under development, and has not been published to pypi*

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

To execute a build pipeline locally, try the following example command:

::
    $ python execute_pipeline.py --pipeline_kwargs={\'sleep_secs\':2} SamplePipeline

To execute a build pipeline remotely, start two consoles and run the following command
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
        --config "../googleapis/pipeline_config/pipeline_logging.yaml:logging_common|logging_python,\
        ../googleapis/pipeline_config/pipeline_common.yaml:default|python" \
        PythonGrpcClientPipeline

    $ python execute_pipeline.py \
        --config "../googleapis/pipeline_config/pipeline_logging.yaml:logging_common|logging_python,\
        ../googleapis/pipeline_config/pipeline_common.yaml:default|python" \
        PythonVkitClientPipeline

To run the Java pipeline:

::
    $ python execute_pipeline.py \
        --config "../googleapis/pipeline_config/pipeline_core.yaml:core,\
        ../googleapis/pipeline_config/pipeline_common.yaml:default|java" \
        JavaCorePipeline

    $ python execute_pipeline.py \
        --config "../googleapis/pipeline_config/pipeline_pubsub.yaml:pubsub_common|pubsub_java,\
        ../googleapis/pipeline_config/pipeline_common.yaml:default|java" \
        JavaGrpcClientPipeline

    $ python execute_pipeline.py \
        --config "../googleapis/pipeline_config/pipeline_pubsub.yaml:pubsub_common|pubsub_java,\
        ../googleapis/pipeline_config/pipeline_common.yaml:default|java" \
        JavaVkitClientPipeline

To run the Go pipeline, first the core protos have to be compiled into the output directory.
Note: this won't be necessary once a public repository for core proto pb.go files.

::
    $ python execute_pipeline.py \
       --config "../googleapis/pipeline_config/pipeline_core.yaml:core,\
       ../googleapis/pipeline_config/pipeline_logging.yaml:logging_go,\
       ../googleapis/pipeline_config/pipeline_common.yaml:default|go" \
       GoCoreProtoPipeline

The actual Go pipeline is as follows:

::
    $ python execute_pipeline.py \
       --config "../googleapis/pipeline_config/pipeline_logging.yaml:logging_common|logging_go|logging_type,\
       ../googleapis/pipeline_config/pipeline_common.yaml:default|go" \
       GoCoreProtoPipeline

    $ python execute_pipeline.py \
       --config "../googleapis/pipeline_config/pipeline_logging.yaml:logging_common|logging_go,\
       ../googleapis/pipeline_config/pipeline_common.yaml:default|go" \
       GoGrpcClientPipeline

    $ python execute_pipeline.py \
       --config "../googleapis/pipeline_config/pipeline_logging.yaml:logging_common|logging_go,\
       ../googleapis/pipeline_config/pipeline_common.yaml:default|go" \
       GoVkitClientPipeline


Pipeline config files
---------------------

Pipeline config files contains configuration data to run pipeline tasks.

googleapis/pipeline_config/pipeline_common.yaml

- default: Default configuration for all pipelines
- {language}: Language specific configuration

googleapis/pipeline_config/pipeline_{API}.yaml

- {API}_common: cross language API specific configuration
- {API}_{language}: API x language configurations


Python Versions
---------------

artman is currently tested with Python 2.7.


Contributing
------------

Contributions to this library are always welcome and highly encouraged.

See the `CONTRIBUTING`_ documentation for more information on how to get started.

.. _`CONTRIBUTING`: https://github.com/googleapis/artman/blob/master/CONTRIBUTING.rst


Versioning
----------

This library follows `Semantic Versioning`_

It is currently in major version zero (``0.y.z``), which means that anything
may change at any time and the public API should not be considered
stable.

.. _`Semantic Versioning`: http://semver.org/


Details
-------

For detailed documentation of the modules in gax-python, please watch `DOCUMENTATION`_.

.. _`DOCUMENTATION`: https://googleapis-artman.readthedocs.org/


License
-------

BSD - See `LICENSE`_ for more information.

.. _`LICENSE`: https://github.com/googleapis/gax-python/blob/master/LICENSE
