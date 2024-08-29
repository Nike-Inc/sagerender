# Copyright 2024-present, Nike, Inc.
# All rights reserved.
#
# This source code is licensed under the Apache-2.0 license found in
# the LICENSE file in the root directory of this source tree.

"""Module for executing AWS SageMaker Pipelines.

This module provides functionality for running SageMaker Pipelines that have been
defined and deployed using the SageRender tool. It includes support for both local
and remote execution of pipelines.

The module provides a command line interface for running pipelines, with options for
specifying the pipeline name, execution parameters, and more. It also includes utility
functions for parsing command line arguments and setting up the execution context.

In addition, this module handles logging and error handling for pipeline execution,
ensuring that any issues encountered during execution are properly reported.
"""

import argparse
import logging
import sys

import boto3
from botocore.exceptions import ClientError, WaiterError
from sagemaker.session import Session
from sagemaker.workflow.pipeline import Pipeline

from sagerender.exceptions import SagemakerPipelineException
from sagerender.utilities.common import setup_logger

logger = logging.getLogger(__name__)


EXPIRED_TOKEN_EXCEPTION = "ExpiredTokenException"
RESOURCE_NOT_FOUND = "ResourceNotFound"


def wait_for_pipeline_execution(execution):
    # 'Executing'|'Stopping'|'Stopped'|'Failed'|'Succeeded'
    while True:
        try:
            execution.wait()
        except WaiterError as error:
            if error.last_response["Error"]["Code"] == EXPIRED_TOKEN_EXCEPTION:
                sagemaker_client = boto3.client("sagemaker", region_name="us-west-2")
                execution.sagemaker_session = Session(sagemaker_client=sagemaker_client)
                continue

            status = error.last_response["PipelineExecutionStatus"]
            if status in ["Executing", "Stopping"]:
                continue
            elif status == "Succeeded":
                logger.info(f"{execution.arn} succeeded")
                break
            elif status == "Failed":
                raise SagemakerPipelineException(
                    f"{error.last_response['PipelineExecutionArn']} failed "
                    f"with error {error.last_response['FailureReason']}"
                ) from error
            elif status == "Stopped":
                logger.warning(f"{error.last_response['PipelineExecutionArn']} stopped.")
                break
            else:
                raise SagemakerPipelineException(
                    f"{error.last_response['PipelineExecutionArn']} with "
                    f"unknown status: {status}"
                ) from error


def parse_args(argv):
    parser = argparse.ArgumentParser(prog="sagerender run-pipeline")
    parser.add_argument(
        "--pipeline-name", required=True, help="Name of the SageMaker pipeline"
    )
    parser.add_argument(
        "--region-name",
        required=False,
        default="us-west-2",
        help="Name of the AWS Region",
    )
    parser.add_argument(
        "--wait",
        "-w",
        action="store_true",
        help="Wait for pipeline execution. Note: Be wary of credentials timeout.",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )
    parser.add_argument(
        "--parameters",
        nargs="+",
        metavar="KEY=VALUE",
        help="Parameters to pass to the pipeline "
        "(e.g., --parameters Param1=Value1 Param2=Value2)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode to dump logs to the local terminal",
    )
    return parser.parse_known_args(argv)


def main(argv=None):
    args, others = parse_args(argv)
    setup_logger(logger, args.verbose)

    sagemaker_client = boto3.client("sagemaker", region_name=args.region_name)

    sagemaker_session = Session(sagemaker_client=sagemaker_client)

    # TODO: Add support for passing in parameters to pipeline
    pipeline = Pipeline(name=args.pipeline_name, sagemaker_session=sagemaker_session)

    # Check if pipeline exists
    try:
        pipeline.describe()
    except ClientError as error:
        if error.response["Error"]["Code"] == RESOURCE_NOT_FOUND:
            raise SagemakerPipelineException(
                error.response["Error"]["Message"]
            ) from error
        raise error from error
    except Exception as error:
        logger.exception("Unknown error when describing pipeline")
        raise error

    logger.info(f"Executing Pipeline: {args.pipeline_name}")
    if args.parameters:
        execution = pipeline.start(
            parameters={
                "name": args.pipeline_name,
                **dict(kv.split("=", 1) for kv in args.parameters),
            }
        )
    else:
        execution = pipeline.start()
    logger.info(f"Pipeline Execution ARN: {execution.arn}")
    if args.debug:
        # Enable debug mode to dump logs to the local terminal
        execution.sagemaker_session.logs_for_pipeline_execution(execution.arn, wait=True)

    if args.wait:
        wait_for_pipeline_execution(execution)


if __name__ == "__main__":
    main(sys.argv)
