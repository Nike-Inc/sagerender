# Copyright 2024-present, Nike, Inc.
# All rights reserved.
#
# This source code is licensed under the Apache-2.0 license found in
# the LICENSE file in the root directory of this source tree.

import unittest
from unittest import mock

import yaml
from parameterized import parameterized
from sagerender.cli.upsert_pipeline import main as upsert_pipeline_main
from sagerender.defaults import CERBERUS, TAGS


class TestCliUpsertPipeline(unittest.TestCase):
    def setUp(self):
        self.pipeline_cfg = yaml.safe_load(open("tests/config/test_pipeline.yaml"))
        self.execution_role = "arn:aws:iam::123456789:role/test-role"
        self.resource_cfg = {
            "execution_role": self.execution_role,
            "region": "us-west-2",
            "security_group_ids": ["sg-123456789"],
            "subnets": ["subnet-123", "subnet-456", "subnet-789"],
        }

    def get_definition_side_effect(self, key, throw_error_on_missing_key=True):
        print(f"{key} DEBUG")
        return self.pipeline_cfg[key]

    @parameterized.expand(["test-pipeline", "test-pipeline-with-configured-options"])
    @mock.patch("sagerender.builder.pipeline.ParallelismConfiguration")
    @mock.patch("sagerender.builder.pipeline.Pipeline.create")
    @mock.patch("sagerender.cli.upsert_pipeline.get_resource_config")
    @mock.patch("sagerender.cli.upsert_pipeline.PipelineBlueprint")
    def test_upsert_pipeline(
        self,
        test_pipeline_name,
        mock_pipeline_blueprint,
        mock_resource_config,
        mock_pipeline_create,
        mock_parallelism_config,
    ):
        mock_resource_config.return_value = self.resource_cfg

        mock_blueprint = mock.Mock()
        mock_parallelism_config_return_value = mock.Mock()
        mock_pipeline_blueprint.return_value = mock_blueprint
        mock_blueprint.get_definition.side_effect = self.get_definition_side_effect
        mock_parallelism_config.return_value = mock_parallelism_config_return_value

        upsert_pipeline_main(
            [
                "--pipeline-name",
                test_pipeline_name,
                "--default-bucket-prefix",
                "test-bucket-prefix",
                "--team",
                "test",
            ]
        )
        mock_pipeline_blueprint.assert_called_once()
        mock_blueprint.create.assert_called_once()
        mock_blueprint.set_context.assert_called_once_with("team", "test")
        mock_resource_config.assert_called_once_with(
            cerberus_cfg=self.pipeline_cfg[CERBERUS]
        )
        mock_blueprint.get_definition.assert_called_with(key=TAGS)
        mock_pipeline_create.assert_called_once_with(
            self.execution_role,
            None,
            self.pipeline_cfg[TAGS],
            (
                mock_parallelism_config_return_value
                if test_pipeline_name.endswith("-with-configured-options")
                else None
            ),
        )
        if test_pipeline_name.endswith("-with-configured-options"):
            mock_parallelism_config.assert_called_once_with(
                max_parallel_execution_steps=5
            )

    @mock.patch("sagerender.cli.upsert_pipeline.get_resource_config")
    @mock.patch("sagerender.cli.upsert_pipeline.PipelineBlueprint")
    def test_upsert_pipeline_with_dry_run(
        self, mock_pipeline_blueprint, mock_resource_config
    ):
        mock_resource_config.return_value = self.resource_cfg

        mock_blueprint = mock.Mock()
        mock_pipeline_blueprint.return_value = mock_blueprint
        mock_blueprint.get_definition.side_effect = self.get_definition_side_effect

        upsert_pipeline_main(["--pipeline-name", "test-pipeline", "--dry-run"])
        mock_pipeline_blueprint.assert_called_once()
        mock_blueprint.create.assert_called_once()
        mock_resource_config.assert_called_once_with(
            cerberus_cfg=self.pipeline_cfg[CERBERUS]
        )
        mock_blueprint.get_definition.assert_called_with(key=TAGS)

    @mock.patch("sagerender.builder.pipeline.Pipeline.start")
    @mock.patch("sagerender.builder.pipeline.Pipeline.create")
    @mock.patch("sagerender.cli.upsert_pipeline.get_resource_config")
    @mock.patch("sagerender.cli.upsert_pipeline.PipelineBlueprint")
    def test_upsert_pipeline_with_local(
        self,
        mock_pipeline_blueprint,
        mock_resource_config,
        mock_pipeline_create,
        mock_pipeline_start,
    ):
        mock_resource_config.return_value = self.resource_cfg

        mock_blueprint = mock.Mock()
        mock_pipeline_blueprint.return_value = mock_blueprint
        mock_blueprint.get_definition.side_effect = self.get_definition_side_effect

        upsert_pipeline_main(["--pipeline-name", "test-pipeline", "--local"])
        mock_pipeline_blueprint.assert_called_once()
        mock_blueprint.create.assert_called_once()
        mock_resource_config.assert_called_once_with(
            cerberus_cfg=self.pipeline_cfg[CERBERUS]
        )
        mock_blueprint.get_definition.assert_called_with(key=TAGS)
        mock_pipeline_create.assert_called_once_with(
            self.execution_role,
            None,
            self.pipeline_cfg[TAGS],
            None,
        )
        mock_pipeline_start.assert_called_once_with(parameters=None)


if __name__ == "__main__":
    unittest.main()
