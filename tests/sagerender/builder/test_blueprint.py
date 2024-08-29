# Copyright 2024-present, Nike, Inc.
# All rights reserved.
#
# This source code is licensed under the Apache-2.0 license found in
# the LICENSE file in the root directory of this source tree.

import os
import unittest
from unittest.mock import patch

from parameterized import parameterized
from sagerender.builder.blueprint import PipelineBlueprint
from sagerender.defaults import CERBERUS, SAGERENDER_HIERA_FILE, TAGS
from sagerender.exceptions import PipelineBlueprintValidationError


class TestPipelineBlueprint(unittest.TestCase):
    @parameterized.expand(["test", "dev", "prod"])
    @patch.dict(os.environ, {SAGERENDER_HIERA_FILE: "examples/simple/hiera.yaml"})
    def test_blueprint_set_context_kv(self, test_env):
        pipeline_blueprint = PipelineBlueprint()
        context = {
            "env": test_env,
            "team": "sagerender",
        }

        for key, value in context.items():
            pipeline_blueprint.set_context(key, value)

        self.assertDictEqual(context, pipeline_blueprint.context)

    @parameterized.expand(["test", "dev", "prod"])
    @patch.dict(os.environ, {SAGERENDER_HIERA_FILE: "examples/simple/hiera.yaml"})
    def test_blueprint_set_context_dict(self, test_env):
        pipeline_blueprint = PipelineBlueprint()
        context = {
            "env": test_env,
            "team": "sagerender",
        }

        pipeline_blueprint.set_context(context)

        self.assertDictEqual(context, pipeline_blueprint.context)

    @parameterized.expand(["test", "dev", "prod"])
    @patch.dict(os.environ, {SAGERENDER_HIERA_FILE: "examples/simple/hiera.yaml"})
    def test_blueprint_get_definition(self, test_env):
        pipeline_name = "local-pipeline"

        pipeline_blueprint = PipelineBlueprint()
        context = {
            "env": test_env,
            "team": "sagerender",
        }

        pipeline = {
            "name": f"{test_env}-local-pipeline",
            "processor-step": {
                "processor": "sagemaker.workflow.steps:Processor",
                "processor_kwargs": {
                    "base_job_name": f"local-test-job-{test_env}",
                    "instance_type": "ml.t3.medium",
                    "instance_count": 1,
                    "image_uri": "141212562619.dkr.ecr.us-west-2.amazonaws.com/"
                    "sagerender:latest",
                    "entrypoint": ["echo"],
                },
                "step_kwargs": {"arguments": ["environment", "executed", test_env]},
            },
        }

        for key, value in context.items():
            pipeline_blueprint.set_context(key, value)

        pipeline_blueprint.create()

        self.assertListEqual(
            [{"Key": "team", "Value": context["team"]}],
            pipeline_blueprint.get_definition(TAGS),
        )

        prefix = "cp" if test_env == "prod" else "ct"

        self.assertDictEqual(
            {
                "sdb": {
                    "team": f"app/{prefix}-commercial0-uswest2-sagerender/" "team_info",
                    "network": f"app/{prefix}-commercial0-uswest2-sagerender/" "network",
                }
            },
            pipeline_blueprint.get_definition(CERBERUS),
        )
        self.assertDictEqual(pipeline, pipeline_blueprint.get_definition(pipeline_name))

    @patch.dict(
        os.environ, {SAGERENDER_HIERA_FILE: "tests/config/missing_context_hiera.yaml"}
    )
    def test_blueprint_throws_error_missing_context(self):
        with self.assertRaises(PipelineBlueprintValidationError):
            _ = PipelineBlueprint()

    @patch.dict(
        os.environ, {SAGERENDER_HIERA_FILE: "tests/config/missing_datadir_hiera.yaml"}
    )
    def test_blueprint_throws_error_missing_datadir(self):
        with self.assertRaises(PipelineBlueprintValidationError):
            _ = PipelineBlueprint()


if __name__ == "__main__":
    unittest.main()
