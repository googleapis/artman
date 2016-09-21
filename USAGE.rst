Usage
=====

Don't use this yet
------------------

**N.B. For now, unless you are part of the googleapis development team, don't try to use this.**

These commands depend on tools that are not yet published, and will currently
 only work in the development environments of the development team.

In particular
- the installation prequisites described need to installed locally
- an as yet unpublished branch of googleapis containing the pipeline configuration should be available
- the pipelines rely on as yet unpublished code-generation tool

Prerequisites
-------------

The pipeline is used to create artifacts in a number of different programming
languages, and needs various tools to do this.

For day-to-day use, these tools should be installed locally.  There is a
Dockerfile_ that sets up the environment with all prerequisites installed, please
use that as a reference for setting up a local environment.

.. _`Dockerfile`: https://github.com/googleapis/artman/blob/master/Dockerfile

Try it out
----------

Local
*****

To execute a build pipeline locally, try the following example command:

  ::

     python execute_pipeline.py \
       --pipeline_kwargs={\'sleep_secs\':2} SamplePipeline

Remote
******

A build pipeline can also be triggered remotely. Run the following command to start a build server:

  ::

     TOOLKIT_HOME=<path_to_toolkit_repo> PATH=<path_to_packman_repo>/bin:$PATH \
       python start_conductor.py --jobboard=<unique_jobboard_name> [--log_local]


And then run this example command to trigger a trivial build on that server
(use the same jobboard name):

  ::

     python execute_pipeline.py \
       --pipeline_kwargs={\'sleep_secs\':2} \
       --env=<unique_jobboard_name> SamplePipeline

Please note, there is no guarantee that your pipeline job will be claimed by the
remote build server unless you choose a unique jobboard name that no one else is using.
Otherwise, it can be picked up by another conductor process.

Config generation
*****************

  ::

     python execute_pipeline.py \
        --config "../googleapis/gapic/api/artman_logging.yaml,\
        ../googleapis/gapic/lang/common.yaml" \
        GapicConfigPipeline


Python (logging)
****************

  ::

     python execute_pipeline.py \
        --config "../googleapis/gapic/api/artman_logging.yaml,\
        ../googleapis/gapic/lang/common.yaml" \
        --language python \
        GrpcClientPipeline

     python execute_pipeline.py \
        --config "../googleapis/gapic/api/artman_logging.yaml,\
        ../googleapis/gapic/lang/common.yaml" \
        --language python \
        GapicClientPipeline

Python also supports a mode that generates dummy proto classes, which allows
Sphinx to generate and link to documentation for proto messages.

  ::

     python execute_pipeline.py \
        --config "../googleapis/gapic/api/artman_logging.yaml,\
        ../googleapis/gapic/lang/doc.yaml" \
        --language python \
        GapicClientPipeline


Java (pubsub)
*************

  ::

     python execute_pipeline.py \
        --config "../googleapis/gapic/core/artman_core.yaml,\
        ../googleapis/gapic/lang/common.yaml" \
        --language java
        GrpcClientPipeline

     python execute_pipeline.py \
        --config "../googleapis/gapic/api/artman_pubsub.yaml,\
        ../googleapis/gapic/lang/common.yaml" \
        --language java \
        GrpcClientPipeline

     python execute_pipeline.py \
        --config "../googleapis/gapic/api/artman_pubsub.yaml,\
        ../googleapis/gapic/lang/common.yaml" \
        --language java \
        GapicClientPipeline


Go (logging)
************

To run the Go pipeline, first the core protos have to be compiled into the
output directory.  Note: this won't be necessary once there is a public
repository for the core proto pb.go files.

  ::

     python execute_pipeline.py \
       --config "../googleapis/gapic/core/artman_core.yaml,\
       ../googleapis/gapic/api/artman_logging.yaml,\
       ../googleapis/gapic/lang/common.yaml" \
       --language go \
       CoreProtoPipeline


The actual Go pipeline is as follows:

  ::

     python execute_pipeline.py \
       --config "../googleapis/gapic/api/artman_logging.yaml,\
       ../googleapis/gapic/lang/common.yaml" \
       --language go \
       CoreProtoPipeline

     python execute_pipeline.py \
       --config "../googleapis/gapic/api/artman_logging.yaml,\
       ../googleapis/gapic/lang/common.yaml" \
       --language go \
       GrpcClientPipeline

     python execute_pipeline.py \
       --config "../googleapis/gapic/api/artman_logging.yaml,\
       ../googleapis/gapic/lang/common.yaml" \
       --language go \
       GapicClientPipeline


C# (pubsub)
***********

  ::

     python execute_pipeline.py \
       --config "../googleapis/gapic/api/artman_pubsub.yaml,\
       ../googleapis/gapic/lang/common.yaml" \
       --language csharp \
       CoreProtoPipeline

     python execute_pipeline.py \
       --config "../googleapis/gapic/api/artman_pubsub.yaml,\
       ../googleapis/gapic/lang/common.yaml" \
       --language csharp \
       GrpcClientPipeline

     python execute_pipeline.py \
       --config "../googleapis/gapic/api/artman_pubsub.yaml,\
       ../googleapis/gapic/lang/common.yaml" \
       --language csharp \
       GapicClientPipeline


Ruby (logging)
****************

  ::

     python execute_pipeline.py \
        --config "../googleapis/gapic/api/artman_logging.yaml,\
        ../googleapis/gapic/lang/common.yaml" \
       --language ruby \
        GrpcClientPipeline

     python execute_pipeline.py \
        --config "../googleapis/gapic/api/artman_logging.yaml,\
        ../googleapis/gapic/lang/common.yaml" \
       --language ruby \
        GapicClientPipeline

Ruby also supports a mode that generates dummy proto classes, which allows
YARD to generate and link to documentation for proto messages.

  ::

     python execute_pipeline.py \
        --config "../googleapis/gapic/api/artman_logging.yaml,\
        ../googleapis/gapic/lang/doc.yaml" \
        --language ruby \
        GapicClientPipeline


Node.JS (logging)
****************

  ::

     python execute_pipeline.py \
        --config "../googleapis/gapic/api/artman_logging.yaml,\
        ../googleapis/gapic/lang/common.yaml" \
       --language nodejs \
        GrpcClientPipeline

     python execute_pipeline.py \
        --config "../googleapis/gapic/api/artman_logging.yaml,\
        ../googleapis/gapic/lang/common.yaml" \
       --language nodejs \
        GapicClientPipeline


Gapic Batch Pipeline
********************

The GAPIC batch pipeline can be used to generate multiple API and language
combinations with one artman command. This example uses the staging repository
batch config file in the googleapis repository, and puts the output in the
staging repository.

  ::

     python execute_pipeline.py \
        --config "../googleapis/gapic/batch/common.yaml" \
        --stage_output GapicClientBatchPipeline


Pipeline configuration
----------------------

artman build pipelines are configured using YAML files with configuration data to
run pipeline tasks.

googleapis/gapic/lang/pipeline_common.yaml

- common: Default configuration for all pipelines
- {language}: Language specific configuration

googleapis/gapic/api/artman_{API}.yaml

- common: cross language API specific configuration
- {language}: API x language configurations
