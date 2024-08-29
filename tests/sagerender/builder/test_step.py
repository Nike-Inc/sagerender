# Copyright 2024-present, Nike, Inc.
# All rights reserved.
#
# This source code is licensed under the Apache-2.0 license found in
# the LICENSE file in the root directory of this source tree.

import unittest
from typing import Dict
from unittest import mock

import pytest
import yaml
from parameterized import parameterized
from sagemaker.automl.automl import AutoML
from sagemaker.estimator import Estimator
from sagemaker.lambda_helper import Lambda
from sagemaker.model import Model
from sagemaker.network import NetworkConfig
from sagemaker.processing import Processor
from sagemaker.transformer import Transformer
from sagemaker.tuner import HyperparameterTuner
from sagemaker.workflow.automl_step import AutoMLStep
from sagemaker.workflow.callback_step import CallbackStep
from sagemaker.workflow.check_job_config import CheckJobConfig
from sagemaker.workflow.clarify_check_step import ClarifyCheckStep
from sagemaker.workflow.condition_step import ConditionStep
from sagemaker.workflow.emr_step import EMRStep, EMRStepConfig
from sagemaker.workflow.fail_step import FailStep
from sagemaker.workflow.lambda_step import LambdaStep
from sagemaker.workflow.model_step import ModelStep
from sagemaker.workflow.notebook_job_step import NotebookJobStep
from sagemaker.workflow.pipeline_context import LocalPipelineSession
from sagemaker.workflow.quality_check_step import QualityCheckStep
from sagemaker.workflow.steps import (
    ProcessingStep,
    TrainingStep,
    TransformStep,
    TuningStep,
)
from sagerender.builder.step import (
    AutoMLStepModel,
    CallbackStepModel,
    CheckStepStepModel,
    ConditionStepModel,
    EMRStepModel,
    FailStepModel,
    LambdaStepModel,
    ModelStepModel,
    NotebookJobStepModel,
    ProcessingStepModel,
    TrainingStepModel,
    TransformStepModel,
    TuningStepModel,
)
from sagerender.defaults import FACTORY_ENUM, FACTORY_FUNCTION
from sagerender.utilities.common import resolve_enum_name, resolve_package_name


class BaseTestStepModelSetup(unittest.TestCase):
    def setUp(self) -> None:
        self.network_config = NetworkConfig(
            security_group_ids=["sg-123456789"],
            subnets=["subnet-123", "subnet-456", "subnet-789"],
        )
        self.sagemaker_session = LocalPipelineSession()
        self.role_arn = "arn:aws:iam::123456789:role/test-role"
        self.step_config = yaml.safe_load(open("tests/config/test_steps.yaml", "rb"))

    def build_step_helper(self, step):
        for k, v in {
            "role": self.role_arn,
            "sagemaker_session": self.sagemaker_session,
            "security_group_ids": self.network_config.security_group_ids,
            "subnets": self.network_config.subnets,
        }.items():
            setattr(step, k, v)

        return step.build()

    def resolve_factory_function(self, config: Dict):
        for key in config:
            if key == FACTORY_FUNCTION:
                return resolve_package_name(config[key])(
                    **self.resolve_factory_function(config["kwargs"])
                )
            elif key == FACTORY_ENUM:
                return resolve_enum_name(config[key])
            elif isinstance(config[key], dict):
                config[key] = self.resolve_factory_function(config[key])
            elif isinstance(config[key], list):
                for idx, argument in enumerate(config[key]):
                    if isinstance(argument, dict):
                        config[key][idx] = self.resolve_factory_function(argument)
                    else:
                        config[key][idx] = argument
            elif isinstance(config[key], str):
                continue

        return config


class TestAutoMLStepModel(BaseTestStepModelSetup):
    def test_automl_step_model(self):
        automl_step_config = self.step_config["automl-step"]

        self.resolve_factory_function(automl_step_config)

        automl_step = AutoMLStepModel.model_validate(automl_step_config)

        actual_step = self.build_step_helper(automl_step)

        expected_step = AutoMLStep(
            name=automl_step_config["name"],
            step_args=AutoML(
                role=self.role_arn,
                sagemaker_session=self.sagemaker_session,
                vpc_config={
                    "SecurityGroupIds": self.network_config.security_group_ids,
                    "Subnets": self.network_config.subnets,
                },
                **automl_step_config["automl_kwargs"],
            ).fit(**automl_step_config["fit_kwargs"]),
            cache_config=automl_step_config.get("cache_config"),
            depends_on=automl_step_config.get("depends_on"),
            retry_policies=automl_step_config.get("retry_policies"),
        )

        self.assertDictEqual(expected_step.to_request(), actual_step.to_request())


class TestCallbackStepModel(BaseTestStepModelSetup):
    def test_callback_step_model(self):
        callback_step_config = self.step_config["callback-step"]

        self.resolve_factory_function(callback_step_config)

        callback_step = CallbackStepModel.model_validate(callback_step_config)

        actual_step = self.build_step_helper(callback_step)

        expected_step = CallbackStep(
            name=callback_step_config["name"],
            sqs_queue_url=callback_step_config["sqs_queue_url"],
            inputs=callback_step_config["inputs"],
            outputs=callback_step_config["outputs"],
            cache_config=callback_step_config.get("cache_config"),
            depends_on=callback_step_config.get("depends_on"),
        )

        self.assertDictEqual(expected_step.to_request(), actual_step.to_request())


class TestLambdaStepModel(BaseTestStepModelSetup):
    def test_lambda_step_model(self):
        lambda_step_config = self.step_config["lambda-step"]

        self.resolve_factory_function(lambda_step_config)

        lambda_step = LambdaStepModel.model_validate(lambda_step_config)

        actual_step = self.build_step_helper(lambda_step)

        lambda_func = Lambda(
            session=self.sagemaker_session,
            vpc_config={
                "SecurityGroupIds": self.network_config.security_group_ids,
                "Subnets": self.network_config.subnets,
            },
            execution_role_arn=self.role_arn,
            **lambda_step_config["lambda_func_kwargs"],
        )

        expected_step = LambdaStep(
            name=lambda_step_config["name"],
            lambda_func=lambda_func,
            inputs=lambda_step_config["inputs"],
            outputs=lambda_step_config["outputs"],
            cache_config=lambda_step_config.get("cache_config"),
            depends_on=lambda_step_config.get("depends_on"),
        )

        self.assertDictEqual(expected_step.to_request(), actual_step.to_request())


class TestNotebookJobStepModel(BaseTestStepModelSetup):
    @pytest.mark.skip(
        reason="`sagemaker_session` is not supported by NotebookJobStep"
        " though included in docstring. Bug needs to be fixed in"
        " the python sagemaker-sdk."
    )
    def test_notebook_job_step_model(self):
        notebook_job_step_config = self.step_config["notebook-job-step"]

        notebook_job_step = NotebookJobStepModel.model_validate(notebook_job_step_config)

        actual_step = self.build_step_helper(notebook_job_step)

        expected_step = NotebookJobStep(
            name=notebook_job_step_config["name"],
            role=self.role_arn,
            sagemaker_session=self.sagemaker_session,
            security_group_ids=self.network_config.security_group_ids,
            subnets=self.network_config.subnets,
            depends_on=notebook_job_step_config.get("depends_on"),
            retry_policies=notebook_job_step_config.get("retry_policies"),
            **notebook_job_step_config["notebook_job_kwargs"],
        )

        self.assertDictEqual(expected_step.to_request(), actual_step.to_request())


class TestProcessingStepModel(BaseTestStepModelSetup):
    @parameterized.expand(
        [
            "processing-step",  # Base
            "processing-step-with-cache-config",  # Cache Config
            "processing-step-with-retry-policies",  # Retry Policies
            "processing-step-with-property-files",  # Property Files
        ]
    )
    def test_processing_model_step(self, test_case):
        processing_step_config = self.step_config[test_case]

        self.resolve_factory_function(processing_step_config)

        processing_step = ProcessingStepModel.model_validate(processing_step_config)

        actual_step = self.build_step_helper(processing_step)

        expected_step = ProcessingStep(
            name=processing_step_config["name"],
            step_args=Processor(
                role=self.role_arn,
                sagemaker_session=self.sagemaker_session,
                network_config=self.network_config,
                **processing_step_config["processor_kwargs"],
            ).run(
                **processing_step_config["step_kwargs"],
            ),
            cache_config=processing_step_config.get("cache_config"),
            depends_on=processing_step_config["depends_on"],
            retry_policies=processing_step_config.get("retry_policies"),
            property_files=processing_step_config.get("property_files"),
            **processing_step.kwargs,
        )

        self.assertDictEqual(expected_step.to_request(), actual_step.to_request())


class TestTrainingStepModel(BaseTestStepModelSetup):
    def test_training_model_step(self):
        train_step_config = self.step_config["train-step"]

        self.resolve_factory_function(train_step_config)

        train_step = TrainingStepModel.model_validate(train_step_config)

        actual_step = self.build_step_helper(train_step)

        expected_step = TrainingStep(
            name=train_step_config["name"],
            step_args=Estimator(
                role=self.role_arn,
                sagemaker_session=self.sagemaker_session,
                subnets=self.network_config.subnets,
                security_group_ids=self.network_config.security_group_ids,
                **train_step_config["estimator_kwargs"],
            ).fit(
                **train_step_config["fit_kwargs"],
            ),
            depends_on=train_step_config["depends_on"],
        )

        self.assertDictEqual(expected_step.to_request(), actual_step.to_request())


class TestTuningStepModel(BaseTestStepModelSetup):
    def test_tuning_step_model(self):
        tune_step_config = self.step_config["tune-step"]

        self.resolve_factory_function(tune_step_config)

        tune_step = TuningStepModel.model_validate(tune_step_config)

        actual_step = self.build_step_helper(tune_step)

        expected_step = TuningStep(
            name=tune_step_config["name"],
            step_args=HyperparameterTuner(
                estimator=Estimator(
                    role=self.role_arn,
                    sagemaker_session=self.sagemaker_session,
                    subnets=self.network_config.subnets,
                    security_group_ids=self.network_config.security_group_ids,
                    **tune_step_config["estimator_kwargs"],
                ),
                **tune_step.tuner_kwargs,
            ).fit(**tune_step.fit_kwargs),
            depends_on=tune_step_config["depends_on"],
        )

        self.assertDictEqual(expected_step.to_request(), actual_step.to_request())


class TestTransformStepModel(BaseTestStepModelSetup):
    def test_transform_step_model(self):
        transform_step_config = self.step_config["transform-step"]

        self.resolve_factory_function(transform_step_config)

        transform_step = TransformStepModel.model_validate(transform_step_config)

        actual_step = self.build_step_helper(transform_step)

        expected_step = TransformStep(
            name=transform_step_config["name"],
            step_args=Transformer(
                sagemaker_session=self.sagemaker_session,
                **transform_step_config["transformer_kwargs"],
            ).transform(**transform_step_config["step_kwargs"]),
            depends_on=transform_step_config["depends_on"],
        )

        self.assertDictEqual(expected_step.to_request(), actual_step.to_request())


class TestCheckStepStepModel(BaseTestStepModelSetup):
    @parameterized.expand(
        [
            "data-bias-clarify-check-step",
            "model-bias-clarify-check-step",
            "model-explainability-clarify-check-step",
        ]
    )
    @mock.patch(
        "sagemaker.workflow.clarify_check_step.ClarifyCheckStep."
        "_upload_monitoring_analysis_config"
    )
    @mock.patch("sagemaker.workflow.clarify_check_step._upload_analysis_config")
    def test_clarify_check_step_model(
        self,
        test_case,
        mock_clarify_upload_analysis_config,
        mock_clarify_upload_monitoring_analysis_config,
    ):
        clarify_check_step_config = self.step_config[test_case]

        mock_clarify_upload_analysis_config.return_value = (
            "s3://some-bucket/some-prefix/data-bias-analysis-output-path"
        )
        mock_clarify_upload_monitoring_analysis_config.return_value = (
            "s3://some-bucket/some-prefix/data-bias-analysis-output-path"
        )

        self.resolve_factory_function(clarify_check_step_config)

        clarify_check_step = CheckStepStepModel.model_validate(clarify_check_step_config)

        actual_step = self.build_step_helper(clarify_check_step)

        expected_step = ClarifyCheckStep(
            name=clarify_check_step_config["name"],
            check_job_config=CheckJobConfig(
                role=self.role_arn,
                sagemaker_session=self.sagemaker_session,
                network_config=NetworkConfig(
                    security_group_ids=self.network_config.security_group_ids,
                    subnets=self.network_config.subnets,
                ),
                **clarify_check_step_config["check_job_config_kwargs"],
            ),
            clarify_check_config=clarify_check_step_config["clarify_check_config"],
            skip_check=clarify_check_step_config.get("skip_check"),
            register_new_baseline=clarify_check_step_config.get("register_new_baseline"),
            supplied_baseline_constraints=clarify_check_step_config.get(
                "supplied_baseline_constraints"
            ),
            model_package_group_name=clarify_check_step_config.get(
                "model_package_group_name"
            ),
            cache_config=clarify_check_step_config.get("cache_config"),
            depends_on=clarify_check_step_config.get("depends_on"),
        )

        self.maxDiff = None

        self.assertDictEqual(expected_step.to_request(), actual_step.to_request())

    @parameterized.expand(
        [
            "data-quality-check-step",  # DataQuality Check
            "model-quality-check-step",  # ModelQuality Check
        ]
    )
    def test_quality_check_step_model(self, test_case):
        quality_check_step_config = self.step_config[test_case]

        self.resolve_factory_function(quality_check_step_config)

        quality_check_step = CheckStepStepModel.model_validate(quality_check_step_config)

        actual_step = self.build_step_helper(quality_check_step)

        expected_step = QualityCheckStep(
            name=quality_check_step_config["name"],
            check_job_config=CheckJobConfig(
                role=self.role_arn,
                sagemaker_session=self.sagemaker_session,
                network_config=NetworkConfig(
                    security_group_ids=self.network_config.security_group_ids,
                    subnets=self.network_config.subnets,
                ),
                **quality_check_step_config["check_job_config_kwargs"],
            ),
            quality_check_config=quality_check_step_config["quality_check_config"],
            skip_check=quality_check_step_config.get("skip_check"),
            register_new_baseline=quality_check_step_config.get("register_new_baseline"),
            supplied_baseline_statistics=quality_check_step_config.get(
                "supplied_baseline_statistics"
            ),
            supplied_baseline_constraints=quality_check_step_config.get(
                "supplied_baseline_constraints"
            ),
            model_package_group_name=quality_check_step_config.get(
                "model_package_group_name"
            ),
            cache_config=quality_check_step_config.get("cache_config"),
            depends_on=quality_check_step_config.get("depends_on"),
        )

        self.assertDictEqual(expected_step.to_request(), actual_step.to_request())


class TestConditionStepModel(BaseTestStepModelSetup):
    def test_condition_step_model(self):
        condition_step_config = self.step_config["condition-step"]

        self.resolve_factory_function(condition_step_config)

        estimator = resolve_package_name("sagemaker.estimator:Estimator")(
            image_uri="123456789.dkr.ecr.us-west-2.amazonaws.com/repo-name:repo-tag",
            role=self.role_arn,
            sagemaker_session=self.sagemaker_session,
            output_path="s3://some-bucket/some-prefix/model.tar.gz",
            instance_count=1,
            instance_type="ml.t3.medium",
        )

        for step_key in ["if_steps", "else_steps"]:
            condition_step_config[step_key] = [
                TrainingStep(name=name, estimator=estimator)
                for name in condition_step_config[step_key]
            ]

        condition_step = ConditionStepModel.model_validate(condition_step_config)

        actual_step = self.build_step_helper(condition_step)

        expected_step = ConditionStep(
            name=condition_step_config["name"],
            conditions=condition_step_config["conditions"],
            if_steps=condition_step_config["if_steps"],
            else_steps=condition_step_config["else_steps"],
            depends_on=condition_step_config["depends_on"],
        )

        self.assertDictEqual(expected_step.to_request(), actual_step.to_request())


class TestModelStepModel(BaseTestStepModelSetup):
    def test_create_model_step_model(self):
        create_model_step_config = self.step_config["create-model-step"]
        create_model_step = ModelStepModel.model_validate(create_model_step_config)

        actual_step = self.build_step_helper(create_model_step)

        expected_step = ModelStep(
            name=create_model_step_config["name"],
            step_args=Model(
                role=self.role_arn,
                sagemaker_session=self.sagemaker_session,
                vpc_config={
                    "SecurityGroupIds": self.network_config.security_group_ids,
                    "Subnets": self.network_config.subnets,
                },
                **create_model_step_config["model_kwargs"],
            ).create(**create_model_step_config["create_model_kwargs"]),
        )

        self.assertListEqual(expected_step.request_dicts(), actual_step.request_dicts())

    def test_register_model_step_model(self):
        register_model_step_config = self.step_config["register-model-step"]

        self.resolve_factory_function(register_model_step_config)

        register_model_step = ModelStepModel.model_validate(register_model_step_config)

        actual_step = self.build_step_helper(register_model_step)

        expected_step = ModelStep(
            name=register_model_step_config["name"],
            step_args=Model(
                role=self.role_arn,
                sagemaker_session=self.sagemaker_session,
                vpc_config={
                    "SecurityGroupIds": self.network_config.security_group_ids,
                    "Subnets": self.network_config.subnets,
                },
                **register_model_step_config["model_kwargs"],
            ).register(**register_model_step_config["register_model_kwargs"]),
        )

        self.assertListEqual(expected_step.request_dicts(), actual_step.request_dicts())


class TestEMRStepModel(BaseTestStepModelSetup):
    @parameterized.expand(
        [
            "emr-step-with-cluster-id",  # test with cluster id
            "emr-step-with-cluster-config",  # test with cluster config
            "emr-step-with-cache-config",  # test with cache config
        ]
    )
    def test_emr_step_model(self, test_case):
        base_emr_step_config = self.step_config[test_case]

        self.resolve_factory_function(base_emr_step_config)

        emr_step = EMRStepModel.model_validate(base_emr_step_config)

        actual_step = self.build_step_helper(emr_step)

        kwargs = {
            "cluster_id": base_emr_step_config.get("cluster_id"),
            "cluster_config": base_emr_step_config.get("cluster_config"),
            "cache_config": base_emr_step_config.get("cache_config"),
            "execution_role_arn": base_emr_step_config.get("execution_role_arn"),
        }

        expected_step = EMRStep(
            name=base_emr_step_config["name"],
            step_config=EMRStepConfig(**base_emr_step_config["emr_step_config_kwargs"]),
            description=base_emr_step_config["description"],
            display_name=base_emr_step_config["display_name"],
            **kwargs,
        )

        self.assertDictEqual(expected_step.to_request(), actual_step.to_request())


class TestFailStepModel(BaseTestStepModelSetup):
    def test_fail_step_model(self):
        base_fail_step = self.step_config["fail-step"]

        fail_step = FailStepModel.model_validate(base_fail_step)

        actual_step = self.build_step_helper(fail_step)

        expected_step = FailStep(
            name=base_fail_step["name"],
            error_message=base_fail_step["error_message"],
            depends_on=base_fail_step["depends_on"],
        )

        self.assertDictEqual(expected_step.to_request(), actual_step.to_request())


if __name__ == "__main__":
    unittest.main()
