# Copyright 2024-present, Nike, Inc.
# All rights reserved.
#
# This source code is licensed under the Apache-2.0 license found in
# the LICENSE file in the root directory of this source tree.

import unittest
from collections import namedtuple
from unittest import mock

from sagerender.cli.run_pipeline import main as run_pipeline_main


class TestCliRunPipeline(unittest.TestCase):
    @mock.patch("sagerender.cli.run_pipeline.Pipeline")
    @mock.patch("sagerender.cli.run_pipeline.Session")
    @mock.patch("sagerender.cli.run_pipeline.boto3")
    @mock.patch("sagerender.cli.run_pipeline.wait_for_pipeline_execution")
    def test_run_pipeline_without_wait(
        self,
        mock_wait_for_pipeline_execution,
        mock_boto3,
        mock_session,
        mock_pipeline,
    ):
        pipeline_name = "test-pipeline"
        region_name = "us-west-2"
        execution_tuple = namedtuple("ExecutionArn", "arn sagemaker_session")

        mock_client = mock.Mock()
        mock_boto3.client.return_value = mock_client
        mock_sagemaker_session = mock.Mock()
        mock_session.return_value = mock_sagemaker_session
        mock_test_pipeline = mock.Mock()
        mock_pipeline.return_value = mock_test_pipeline
        mock_pipeline.describe.return_value = True
        mock_pipeline.start.return_value = execution_tuple(
            "execution-arn", mock_sagemaker_session
        )

        run_pipeline_main(
            [
                "--pipeline-name",
                pipeline_name,
                "--region-name",
                region_name,
                "--parameters",
                "Param1=Value1",
                "Param2=Value2",
                "--debug",
            ]
        )

        mock_boto3.client.assert_called_once_with("sagemaker", region_name=region_name)
        mock_session.assert_called_once_with(sagemaker_client=mock_client)
        mock_pipeline.assert_called_once_with(
            name=pipeline_name, sagemaker_session=mock_sagemaker_session
        )
        mock_test_pipeline.describe.assert_called_once()
        mock_test_pipeline.start.assert_called_once_with(
            parameters={
                "name": pipeline_name,
                "Param1": "Value1",
                "Param2": "Value2",
            }
        )
        mock_wait_for_pipeline_execution.assert_not_called()


if __name__ == "__main__":
    unittest.main()
