# Copyright 2024-present, Nike, Inc.
# All rights reserved.
#
# This source code is licensed under the Apache-2.0 license found in
# the LICENSE file in the root directory of this source tree.

import unittest
from unittest.mock import MagicMock, call, patch

import yaml
from sagemaker.network import NetworkConfig
from sagemaker.processing import Processor
from sagemaker.workflow.execution_variables import ExecutionVariables
from sagemaker.workflow.functions import Join, JsonGet
from sagemaker.workflow.parameters import ParameterString
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.pipeline_context import LocalPipelineSession
from sagemaker.workflow.properties import PropertyFile
from sagemaker.workflow.retry import (
    SageMakerJobExceptionTypeEnum,
    SageMakerJobStepRetryPolicy,
    StepExceptionTypeEnum,
    StepRetryPolicy,
)
from sagemaker.workflow.steps import CacheConfig, ProcessingStep
from sagerender.builder.pipeline import PipelineBuilder
from sagerender.exceptions import PipelineNotFoundError


class TestPipelineBuilder(unittest.TestCase):
    def test_pipeline_builder(self):
        pipeline_cfg = yaml.safe_load(open("tests/config/test_pipeline_builder.yaml"))

        role_arn = "arn:aws:iam::123456789:role/test-role"
        sagemaker_session = LocalPipelineSession()
        security_group_ids = ["sg-123456789"]
        subnets = ["subnet-123", "subnet-456", "subnet-789"]

        tags = [{"Name": "team", "Value": "test"}]

        param_1 = ParameterString(name="param-1", default_value=None)
        param_2 = ParameterString(name="param-2", default_value="ml.t3.medium")
        param_3 = ParameterString(name="param-3", default_value="ENV_VALUE2")

        network_config = NetworkConfig(
            security_group_ids=security_group_ids, subnets=subnets
        )

        step_0_cfg = pipeline_cfg.copy()

        step_0_cfg["step-0"]["processor_kwargs"]["instance_type"] = param_2
        step_0_cfg["step-0"]["processor_kwargs"]["env"]["ENV_VAR2"] = param_3

        property_files = [
            PropertyFile(name="PropertyFileA", output_name="test0", path="test0.json"),
            PropertyFile(name="PropertyFileB", output_name="test1", path="test1.json"),
        ]

        step_0_kwargs = {
            "arguments": [
                "Hello",
                "World",
                Join(
                    on="/",
                    values=[
                        "s3:/",
                        param_1,
                        ExecutionVariables.PIPELINE_EXECUTION_ID,
                        "model.tar.gz",
                    ],
                ),
            ]
        }

        step_0 = ProcessingStep(
            name=pipeline_cfg["step-0"]["name"],
            step_args=Processor(
                role=role_arn,
                sagemaker_session=sagemaker_session,
                network_config=network_config,
                **step_0_cfg["step-0"]["processor_kwargs"],
            ).run(**step_0_kwargs),
            property_files=property_files,
        )

        cache_config_1 = CacheConfig(
            enable_caching=True,
            expire_after="7d",
        )

        retry_policies = [
            SageMakerJobStepRetryPolicy(
                exception_types=[
                    SageMakerJobExceptionTypeEnum.INTERNAL_ERROR,
                    SageMakerJobExceptionTypeEnum.CAPACITY_ERROR,
                    SageMakerJobExceptionTypeEnum.RESOURCE_LIMIT,
                ],
                interval_seconds=1,
                backoff_rate=2,
                max_attempts=2,
                expire_after_mins=10,
            ),
            StepRetryPolicy(
                exception_types=[
                    StepExceptionTypeEnum.SERVICE_FAULT,
                    StepExceptionTypeEnum.THROTTLING,
                ],
                interval_seconds=1,
                backoff_rate=2,
                max_attempts=2,
                expire_after_mins=10,
            ),
        ]

        step_1_kwargs = {
            "arguments": [
                "/opt/ml/code/test.py",
                param_1,
                JsonGet(
                    step_name=step_0.properties.step_name,
                    property_file=property_files[0],
                    json_path="test0",
                ),
            ]
        }
        step_1 = ProcessingStep(
            name=pipeline_cfg["step-1"]["name"],
            step_args=Processor(
                role=role_arn,
                sagemaker_session=sagemaker_session,
                network_config=network_config,
                **pipeline_cfg["step-1"]["processor_kwargs"],
            ).run(**step_1_kwargs),
            cache_config=cache_config_1,
            retry_policies=retry_policies,
            depends_on=pipeline_cfg["step-1"]["depends_on"],
        )

        expected_pipeline = Pipeline(
            name=pipeline_cfg["name"],
            parameters=[param_1, param_2, param_3],
            steps=[step_0, step_1],
            sagemaker_session=sagemaker_session,
        )

        actual_pipeline = (
            PipelineBuilder()
            .set_name(pipeline_cfg["name"])
            .set_role_arn(role_arn)
            .set_sagemaker_session(sagemaker_session)
            .add_security_group_ids(security_group_ids)
            .add_subnets(subnets)
            .add_parameters(pipeline_cfg["parameters"])
            .add_property_files(pipeline_cfg["property_files"])
            .add_steps(pipeline_cfg)
            .add_tags(tags)
            .build()
        )

        self.assertEqual(
            expected_pipeline.definition(), actual_pipeline.pipeline.definition()
        )

    def test_pipeline_builder_upsert_raise_pipeline_not_found(self):
        pipeline = PipelineBuilder()

        with self.assertRaises(PipelineNotFoundError):
            pipeline.upsert()

    def test_pipeline_builder_run_raise_pipeline_not_found(self):
        pipeline = PipelineBuilder()

        with self.assertRaises(PipelineNotFoundError):
            pipeline.run()

    def test_replace_argument_param(self):
        """Assert that the parameter lookup works."""
        pipeline = PipelineBuilder()
        pipeline.parameters = {"foo": "bar"}

        expected = "bar"
        actual = pipeline._replace_argument("param:foo")
        self.assertEqual(expected, actual)

    def test_replace_argument_exec(self):
        """Assert that the execution Variables are replaced."""
        pipeline = PipelineBuilder()

        # All available execution variables in SageMaker Pipeline
        execution_variables = [
            exec_var
            for exec_var in dir(ExecutionVariables)
            if not exec_var.startswith("__")
        ]

        for execution_variable in execution_variables:
            expected_execution_variable = getattr(ExecutionVariables, execution_variable)

            actual_execution_variable = pipeline._replace_argument(
                f"exec:{execution_variable}"
            )

            self.assertEqual(expected_execution_variable, actual_execution_variable)

    def test_replace_argument_property_file(self):
        """Assert that the propertyFile lookup works."""
        pipeline = PipelineBuilder()
        pipeline.property_files = {"property_foo": "property_bar"}

        expected = "property_bar"
        actual = pipeline._replace_argument("propertyFile:property_foo")
        self.assertEqual(expected, actual)

    def test_replace_argument_no_update(self):
        """Assert that the argument is not replaced if keyword prefix is not specified"""
        pipeline = PipelineBuilder()
        pipeline.parameters = {"foo": "bar"}

        expected = "foo"
        actual = pipeline._replace_argument("foo")
        self.assertEqual(expected, actual)

    def test_replace_step_arguments_join(self):
        """Assert that the argument is replaced by an instance of Join"""
        join_config = yaml.safe_load(
            """
        input:
            factory_function: sagemaker.workflow.functions:Join
            kwargs:
                'on': "/"
                values:
                - s3:/
                - some-bucket
                - some-prefix
                - some-object
        """
        )

        pipeline = PipelineBuilder()
        expected = {"input": Join(**join_config["input"]["kwargs"])}
        actual = pipeline._replace_step_arguments(join_config)

        self.assertEqual(expected, actual)

    def test_replace_step_arguments_jsonget(self):
        """Assert that the argument is replaced by an instance of JsonGet"""
        jsonget_config = yaml.safe_load(
            """
        value:
            factory_function: sagemaker.workflow.functions:JsonGet
            kwargs:
                step_name: test-step
                property_file: TestInfo
                json_path: path.to.value
        """
        )

        pipeline = PipelineBuilder()
        expected = {"value": JsonGet(**jsonget_config["value"]["kwargs"])}
        actual = pipeline._replace_step_arguments(jsonget_config)

        self.assertEqual(expected, actual)

    def test_replace_arguments_complex(self):
        """Assert that the argument is replaced by SageMaker Primitive Types and
        Functions"""
        input_data = yaml.safe_load(
            """
        input:
            location:
                factory_function: sagemaker.workflow.functions:Join
                kwargs:
                    'on': "/"
                    values:
                    - a
                    - param:bucket
                    - exec:START_DATETIME
                    - factory_function: sagemaker.workflow.functions:JsonGet
                      kwargs:
                        step_name: step_name
                        # property_file: propertyFile:ModelInfo
                        s3_uri:
                            factory_function: sagemaker.workflow.functions:Join
                            kwargs:
                              'on': "/"
                              values:
                              - b
                              - exec:PIPELINE_EXECUTION_ARN
                        json_path: model
        """
        )

        pipeline = PipelineBuilder()
        pipeline.parameters = {"bucket": "bucket"}
        pipeline.property_files = {"ModelInfo": "ModelInfoPropertyFile"}

        expected = {
            "input": {
                "location": Join(
                    on="/",
                    values=[
                        "a",
                        "bucket",
                        ExecutionVariables.START_DATETIME,
                        JsonGet(
                            step_name="step_name",
                            s3_uri=Join(
                                on="/",
                                values=["b", ExecutionVariables.PIPELINE_EXECUTION_ARN],
                            ),
                            json_path="model",
                        ),
                    ],
                )
            }
        }

        actual = pipeline._replace_step_arguments(input_data)
        self.assertEqual(expected, actual)

    def test_replace_step_arguments(self):
        """Assert that replace_step_arguments deep searches the dict and
        calls `_replace_argument` with the values."""
        pipeline = PipelineBuilder()
        with patch(
            "sagerender.builder.pipeline.PipelineBuilder._replace_argument"
        ) as mock_replace:
            mock_replace.return_value = "replaced"

            complex_dict = {"foo": "bar", "fuu": ["baz", {"bar": "bazz"}]}
            expected = {"foo": "replaced", "fuu": ["replaced", {"bar": "replaced"}]}

            calls = [call("bar"), call("baz"), call("bazz")]

            actual = pipeline._replace_step_arguments(complex_dict)

            mock_replace.assert_has_calls(calls)

            self.assertDictEqual(expected, actual)

    @patch(
        "sagerender.builder.step.StepModel.model_validate",
        return_value=MagicMock(),
        autospec=True,
    )
    def test_add_step_param_replacement(self, mock_step_model_validate):
        """Assert that add_step kwargs are passed to _replace_step_arguments and
        then passed into StepBuilder"""
        mock_kwargs = MagicMock(autospec=True)

        step_name = "step"

        with patch(
            "sagerender.builder.pipeline.PipelineBuilder._replace_step_arguments"
        ) as mock_replace:
            pipeline = PipelineBuilder()
            role_arn = "role_arn"
            pipeline.set_role_arn(role_arn)
            mock_sagemaker_session = MagicMock()
            security_group_ids = ["sg-123"]
            subnets = ["subnet-123", "subnet-456"]
            pipeline.set_sagemaker_session(mock_sagemaker_session)
            pipeline.add_security_group_ids(security_group_ids)
            pipeline.add_subnets(subnets)
            pipeline.add_step(name=step_name, kwargs=mock_kwargs)
            mock_replace.assert_called_with(mock_kwargs)
            mock_replace().update.assert_called_once_with(
                {
                    "name": mock_replace().get("name", step_name),
                    "role": role_arn,
                    "sagemaker_session": mock_sagemaker_session,
                    "security_group_ids": security_group_ids,
                    "subnets": subnets,
                }
            )
            mock_step_model_validate.assert_called_once_with({"step": mock_replace()})


if __name__ == "__main__":
    unittest.main()
