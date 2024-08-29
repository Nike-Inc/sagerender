# Copyright 2024-present, Nike, Inc.
# All rights reserved.
#
# This source code is licensed under the Apache-2.0 license found in
# the LICENSE file in the root directory of this source tree.

"""Module for creating or updating AWS SageMaker Pipelines.

This module provides functionality for creating new SageMaker Pipelines or updating
existing ones using the SageRender tool. It includes support for both local and remote
deployment of pipelines.

The module provides a command line interface for upserting pipelines, with options for
specifying the pipeline definition file, pipeline name, and more. It also includes
utility functions for parsing command line arguments and setting up the deployment
context.

In addition, this module handles logging and error handling for pipeline upsertion,
ensuring that any issues encountered during the process are properly reported.
"""

import argparse
import logging
import os
import sys
from pprint import pformat

import boto3
from sagemaker.workflow.pipeline_context import LocalPipelineSession, PipelineSession

from sagerender.builder.blueprint import PipelineBlueprint
from sagerender.builder.pipeline import PipelineBuilder
from sagerender.defaults import (
    CERBERUS,
    PIPELINE_EXPERIMENT_CONFIG,
    PIPELINE_PARAMETERS,
    PIPELINE_PROPERTY_FILES,
    PIPELINE_SESSION_BUCKET,
    RESOURCE_CONFIG,
    TAGS,
)
from sagerender.utilities.common import get_resource_config, setup_logger

logger = logging.getLogger(__name__)


def parse_args(argv):
    parser = argparse.ArgumentParser(prog="sagerender upsert-pipeline")
    parser.add_argument(
        "--pipeline-name", required=True, help="Name of the SageMaker pipeline"
    )
    parser.add_argument(
        "--max-parallel-execution-steps",
        required=False,
        help="Set the max parallel execution steps for SageMaker pipeline",
        type=int,
        default=None,
    )
    parser.add_argument(
        "--use-custom-job-prefix",
        required=False,
        help="A feature flag to toggle on/off custom name prefixing during pipeline "
        "orchestration.",
        action="store_true",
    )
    parser.add_argument(
        "--experiment-name",
        required=False,
        help="Name of the pipeline experiment",
    )
    parser.add_argument(
        "--trial-name",
        required=False,
        help="Name of the trial run",
    )
    parser.add_argument(
        "--default-bucket-prefix",
        required=False,
        default=os.getenv("SAGERENDER_DEFAULT_PREFIX"),
        help="Default bucket prefix sets s3 path to be "
        "bucket-prefix/default-bucket-prefix/pipeline-name",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip upserting SageMaker pipeline definition. Used for debugging.",
    )
    parser.add_argument(
        "--local", "-l", action="store_true", help="Run in local pipeline mode"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )
    return parser.parse_known_args(argv)


def main(argv=None):
    args, others = parse_args(argv)

    setup_logger(logger, args.verbose)

    context = {
        others[i].removeprefix("--").replace("-", "_"): others[i + 1]
        for i in range(0, len(others), 2)
    }

    pipeline_blueprint = PipelineBlueprint()
    logger.info("Loading SageMaker Pipeline with the following context...")
    for key, value in context.items():
        logger.info(f"{key}:\t{value}")
        pipeline_blueprint.set_context(key, value)

    # Create pipeline blueprint
    pipeline_blueprint.create()

    resource_cfg = get_resource_config(
        cerberus_cfg=pipeline_blueprint.get_definition(
            key=CERBERUS, throw_error_on_missing_key=False
        )
    ) or pipeline_blueprint.get_definition(
        key=RESOURCE_CONFIG, throw_error_on_missing_key=False
    )

    assert resource_cfg is not None, f"{CERBERUS} or {RESOURCE_CONFIG} must be provided."

    session_bucket = pipeline_blueprint.get_definition(key=PIPELINE_SESSION_BUCKET)

    if not args.local:
        sagemaker_client = boto3.client(
            "sagemaker",
            region_name=resource_cfg["region"],
        )

        sagemaker_session = PipelineSession(
            default_bucket=session_bucket,
            default_bucket_prefix=args.default_bucket_prefix,
            sagemaker_client=sagemaker_client,
        )
    else:
        sagemaker_session = LocalPipelineSession(default_bucket=session_bucket)

    pipeline_steps = pipeline_blueprint.get_definition(key=args.pipeline_name)

    logger.info(f"Pipeline Configuration:\n {pformat(pipeline_steps)}")

    parameters = pipeline_steps.get(PIPELINE_PARAMETERS, {})
    property_files = pipeline_steps.get(PIPELINE_PROPERTY_FILES, {})
    pipeline_name = pipeline_steps.get("name", args.pipeline_name)
    max_parallel_execution_steps = pipeline_steps.get(
        "max_parallel_execution_steps", args.max_parallel_execution_steps
    )
    use_custom_job_prefix = pipeline_steps.get(
        "use_custom_job_prefix", args.use_custom_job_prefix
    )

    pipeline_experiment_config = None
    if PIPELINE_EXPERIMENT_CONFIG in pipeline_steps:
        pipeline_experiment_config = {
            "experiment_name": pipeline_steps.get(PIPELINE_EXPERIMENT_CONFIG, {}).get(
                "experiment_name", args.experiment_name
            ),
            "trial_name": pipeline_steps.get(PIPELINE_EXPERIMENT_CONFIG, {}).get(
                "trial_name", args.trial_name
            ),
        }

    pipeline = (
        PipelineBuilder()
        .set_name(pipeline_name)
        .set_sagemaker_session(sagemaker_session)
        .set_role_arn(resource_cfg["execution_role"])
        .set_max_parallel_execution_steps(max_parallel_execution_steps)
        .set_use_custom_job_prefix(use_custom_job_prefix)
        .set_pipeline_experiment_config(pipeline_experiment_config)
        .add_security_group_ids(resource_cfg["security_group_ids"])
        .add_subnets(resource_cfg["subnets"])
        .add_parameters(parameters)
        .add_property_files(property_files)
        .add_steps(pipeline_steps)
        .add_tags(pipeline_blueprint.get_definition(key=TAGS))
        .build()
    )

    if args.dry_run:
        logger.info(f"SageMaker Pipeline Definition:\n {pipeline.definition()}")
        logger.info("Skipping pipeline upsert due to dry run.")
        return

    logger.info(
        f"Upsert Pipeline: {args.pipeline_name} "
        f"with execution role: {resource_cfg['execution_role']}"
    )
    pipeline.upsert()

    if args.local:
        pipeline.run()


if __name__ == "__main__":
    main(sys.argv)
