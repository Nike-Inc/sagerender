# Copyright 2024-present, Nike, Inc.
# All rights reserved.
#
# This source code is licensed under the Apache-2.0 license found in
# the LICENSE file in the root directory of this source tree.

"""Module for building and managing AWS SageMaker Pipeline Steps.

This module provides the StepModel class, which is used to create and manage
individual steps in a SageMaker pipeline. The StepModel class supports various
types of SageMaker Pipeline Steps.

The StepModel class allows for the configuration of step properties such as
dependencies, network configuration, role, SageMaker session,
cache configuration, and retry policies.
"""

from typing import Annotated, Any, Dict, List, Optional, Union

from pydantic import BaseModel, Discriminator, Tag, model_validator
from sagemaker.network import NetworkConfig
from sagemaker.workflow.automl_step import AutoMLStep
from sagemaker.workflow.callback_step import CallbackStep
from sagemaker.workflow.check_job_config import CheckJobConfig
from sagemaker.workflow.condition_step import ConditionStep
from sagemaker.workflow.emr_step import EMRStep, EMRStepConfig
from sagemaker.workflow.fail_step import FailStep
from sagemaker.workflow.lambda_step import LambdaStep
from sagemaker.workflow.model_step import ModelStep
from sagemaker.workflow.notebook_job_step import NotebookJobStep
from sagemaker.workflow.steps import (
    ProcessingStep,
    TrainingStep,
    TransformStep,
    TuningStep,
)

from sagerender.defaults import RESERVED_STEP_KEYWORDS
from sagerender.exceptions import SagemakerStepException
from sagerender.utilities.common import resolve_package_name


class BaseStepModel(BaseModel):
    """
    Base class for step models that defines common attributes shared across SageMaker
    Pipeline Steps.

    Attributes:
        name (str): The name of the step.
        depends_on (Optional[List]): A list of step names that this step depends on.
        cache_config (Any): Configuration for caching.
        retry_policies (List[Any]): A list of retry policies for this step.
        model_config (dict): Pydantic configuration setting to allow extra fields.
    """

    name: str
    depends_on: Optional[List] = None
    cache_config: Optional[Any] = None
    retry_policies: Optional[List[Any]] = None
    model_config = {"extra": "allow"}

    @property
    def kwargs(self):
        return {
            k: getattr(self, k)
            for k in (
                set(self.model_extra) - set(self.model_fields) - RESERVED_STEP_KEYWORDS
            )
        }


class AutoMLStepModel(BaseStepModel):
    """
    Represents a step model for a SageMaker AutoML step.

    Attributes:
        automl (Optional[str]): The name of the AutoML class to use.
            Defaults to "sagemaker.automl.automl:AutoML".
        automl_kwargs (Dict[str, Any]): Keyword arguments to be passed to the AutoML
            class constructor.
        fit_kwargs (Dict[str, Any]): Keyword arguments to be passed to the `fit` method
            of the AutoML processor.
    """

    automl: Optional[str] = "sagemaker.automl.automl:AutoML"
    automl_kwargs: Dict[str, Any]
    fit_kwargs: Dict[str, Any]

    def build(self):
        """
        Builds and returns a SageMaker AutoMLStep object based on the specified
        attributes.

        Returns:
            AutoMLStep: The built SageMaker AutoMLStep object.
        """

        automl_processor = resolve_package_name(self.automl)(
            role=self.role,
            sagemaker_session=self.sagemaker_session,
            vpc_config={
                "SecurityGroupIds": self.security_group_ids,
                "Subnets": self.subnets,
            },
            **self.automl_kwargs,
        )

        return AutoMLStep(
            name=self.name,
            step_args=automl_processor.fit(**self.fit_kwargs),
            cache_config=self.cache_config,
            depends_on=self.depends_on,
            retry_policies=self.retry_policies,
            **self.kwargs,
        )


class CallbackStepModel(BaseStepModel):
    """
    Represents a step model for a SageMaker Callback step.

    Attributes:
        sqs_queue_url (str): The URL of the SQS queue.
        inputs (Dict): A dictionary of input values.
        outputs (List[Any]): A list of output values.
    """

    sqs_queue_url: str
    inputs: Dict
    outputs: List[Any]

    def build(self):
        """
        Builds and returns a SageMaker CallbackStep object.

        Returns:
            CallbackStep: The built SageMaker CallbackStep object.
        """
        return CallbackStep(
            name=self.name,
            sqs_queue_url=self.sqs_queue_url,
            inputs=self.inputs,
            outputs=self.outputs,
            cache_config=self.cache_config,
            depends_on=self.depends_on,
        )


class CheckStepStepModel(BaseStepModel):
    """
    Represents a step model for a SageMaker Clarify Check or Quality Check step.

    Attributes:
        check_job_config_kwargs (Dict[str, Any]): Keyword arguments for configuring the
            check job.
        clarify_check_config (Optional[Any]): Configuration for the clarify check.
            Default is None.
        quality_check_config (Optional[Any]): Configuration for the quality check.
            Default is None.
    """

    check_job_config_kwargs: Dict[str, Any]
    clarify_check_config: Optional[Any] = None
    quality_check_config: Optional[Any] = None

    @property
    def check_job_config(self):
        """
        Returns a CheckJobConfig object with the specified role, sagemaker_session,
        network_config, and additional keyword arguments.

        Returns:
            CheckJobConfig: The CheckJobConfig object.
        """
        return CheckJobConfig(
            role=self.role,
            sagemaker_session=self.sagemaker_session,
            network_config=NetworkConfig(
                security_group_ids=self.security_group_ids,
                subnets=self.subnets,
            ),
            **self.check_job_config_kwargs,
        )

    @model_validator(mode="after")
    def mutually_exclusive(self):
        """
        Validates that either `clarify_check_config` or `quality_check_config` is
            specified, but not both.

        Raises:
            ValueError: If both `clarify_check_config` and `quality_check_config` are
                specified or if neither is specified.

        Returns:
            self: The current instance of the class.
        """
        if not (self.clarify_check_config is not None) ^ (
            self.quality_check_config is not None
        ):
            raise ValueError(
                "Either specify `clarify_check_config` or `quality_check_config`."
            )
        return self

    def build(self):
        """
        Builds the step based on the provided configuration.

        Returns:
            The built step object.

        Raises:
            RuntimeError: If an unsupported step config is defined.
        """

        if self.clarify_check_config is not None:
            func_name = "sagemaker.workflow.clarify_check_step:ClarifyCheckStep"
            kwargs = {
                **self.kwargs,
                **{"clarify_check_config": self.clarify_check_config},
            }
        elif self.quality_check_config is not None:
            func_name = "sagemaker.workflow.quality_check_step:QualityCheckStep"
            kwargs = {
                **self.kwargs,
                **{"quality_check_config": self.quality_check_config},
            }
        else:
            raise RuntimeError("Unsupported step config defined.")

        return resolve_package_name(func_name)(
            name=self.name,
            check_job_config=self.check_job_config,
            cache_config=self.cache_config,
            depends_on=self.depends_on,
            **kwargs,
        )


class ConditionStepModel(BaseStepModel):
    """
    Represents a step model for a SageMaker Condition step.

    Attributes:
        conditions (List[Any]): The list of conditions for the step.
        if_steps (List[Any]): The list of steps to execute if the conditions are met.
        else_steps (List[Any]): The list of steps to execute if the conditions are not
            met.
    """

    conditions: List[Any]
    if_steps: List[Any]
    else_steps: List[Any]

    def build(self):
        """
        Builds and returns a ConditionStep instance based on the model.

        Returns:
            ConditionStep: The built ConditionStep instance.
        """
        return ConditionStep(
            name=self.name,
            conditions=self.conditions,
            if_steps=self.if_steps,
            else_steps=self.else_steps,
            depends_on=self.depends_on,
            **self.kwargs,
        )


class EMRStepModel(BaseStepModel):
    """
    Represents a step model for a SageMaker EMR step.

    Attributes:
        emr_step_config_kwargs (Dict[str, Any]): Keyword arguments for configuring the
            EMR step.
        cluster_id (Optional[str]): The ID of the EMR cluster. Defaults to None.
        cluster_config (Optional[Dict[str, Any]]): Configuration for the EMR cluster.
            Defaults to None.
        execution_role_arn (Optional[str]): The ARN of the execution role.
            Defaults to None.
        display_name (str): The display name of the EMR step.
        description (str): The description of the EMR step.
    """

    emr_step_config_kwargs: Dict[str, Any]
    cluster_id: Optional[str] = None
    cluster_config: Optional[Dict[str, Any]] = None
    execution_role_arn: Optional[str] = None
    display_name: str
    description: str

    @model_validator(mode="after")
    def mutually_exclusive(self):
        """
        Validates that either `cluster_id` or `cluster_config` is specified, but not
            both.

        Raises:
            ValueError: If both `cluster_id` and `cluster_config` are specified or if
                neither is specified.

        Returns:
            self: The current instance of the class.
        """
        if not (self.cluster_id is not None) ^ (self.cluster_config is not None):
            raise ValueError("Either specify `cluster_id` or `cluster_config`.")
        return self

    def build(self):
        """
        Builds and returns an EMRStep object based on the provided configuration.

        Returns:
            EMRStep: The built EMRStep object.
        """

        emr_step_config = EMRStepConfig(**self.emr_step_config_kwargs)

        # TODO: Default to subnets and security group ids from Cerberus if not configured
        #   as part of the `cluster_config`.
        if self.cluster_id is not None:
            # Default to pipeline execution role if execution role arn is not defined.
            self.execution_role_arn = self.execution_role_arn or self.role

        return EMRStep(
            name=self.name,
            cluster_id=self.cluster_id,
            step_config=emr_step_config,
            cluster_config=self.cluster_config,
            execution_role_arn=self.execution_role_arn,
            cache_config=self.cache_config,
            depends_on=self.depends_on,
            display_name=self.display_name,
            description=self.description,
        )


class FailStepModel(BaseStepModel):
    """
    Represents a step model for a SageMaker Fail step.

    Attributes:
        error_message (Any): The error message associated with the fail step.
    """

    error_message: Any

    def build(self):
        """
        Build and return a FailStep instance.

        Returns:
            FailStep: The built FailStep instance.
        """
        return FailStep(
            name=self.name,
            error_message=self.error_message,
            depends_on=self.depends_on,
            **self.kwargs,
        )


class LambdaStepModel(BaseStepModel):
    """
    Represents a step model for a SageMaker Lambda step.

    Attributes:
        lambda_func (Optional[str]): The name of the Lambda function to be executed.
            Defaults to "sagemaker.lambda_helper:Lambda".
        lambda_func_kwargs (Dict[str, Any]): Keyword arguments to be passed to the
            Lambda function.
        inputs (Dict): The inputs for the Lambda step.
        outputs (List[Any]): The outputs for the Lambda step.
    """

    lambda_func: Optional[str] = "sagemaker.lambda_helper:Lambda"
    lambda_func_kwargs: Dict[str, Any]
    inputs: Optional[Dict] = None
    outputs: Optional[List[Any]] = None

    def build(self):
        """
        Builds and returns a LambdaStep instance based on the attributes of the
        LambdaStepModel.

        Returns:
            LambdaStep: The built LambdaStep instance.
        """

        if "execution_role_arn" not in self.lambda_func_kwargs:
            self.lambda_func_kwargs["execution_role_arn"] = self.role

        lambda_func = resolve_package_name(self.lambda_func)(
            session=self.sagemaker_session,
            vpc_config={
                "SecurityGroupIds": self.security_group_ids,
                "Subnets": self.subnets,
            },
            **self.lambda_func_kwargs,
        )

        return LambdaStep(
            name=self.name,
            lambda_func=lambda_func,
            inputs=self.inputs,
            outputs=self.outputs,
            cache_config=self.cache_config,
            depends_on=self.depends_on,
            **self.kwargs,
        )


class ModelStepModel(BaseStepModel):
    """
    Represents a step model for a SageMaker ModelStep step that can be used to either
    create or register a SageMaker model.

    Attributes:
        model (Optional[str]): The model class to be used. Defaults to
            "sagemaker.model:Model".
        model_kwargs (Dict[str, Any]): The keyword arguments to be passed to the model
            class constructor.
        create_model_kwargs (Optional[Dict[str, Any]]): The keyword arguments to be
            passed to the `create` method of the model class.
        register_model_kwargs (Optional[Dict[str, Any]]): The keyword arguments to be
            passed to the `register` method of the model class.
        retry_policies (Union[Dict[str, Any], List[Dict[str, Any]]]): The retry policies
            to be applied.
    """

    model: Optional[str] = "sagemaker.model:Model"
    model_kwargs: Dict[str, Any]
    create_model_kwargs: Optional[Dict[str, Any]] = None
    register_model_kwargs: Optional[Dict[str, Any]] = None
    retry_policies: Optional[Union[Dict[str, Any], List[Any]]] = None

    @model_validator(mode="after")
    def mutually_exclusive(self):
        """
        Validates that only one of `create_model_kwargs` or `register_model_kwargs`
            is specified.

        Raises:
            ValueError: If both `create_model_kwargs` and `register_model_kwargs` are
                specified or if neither is specified.

        Returns:
            self: The current instance of the class.
        """
        if not (self.create_model_kwargs is not None) ^ (
            self.register_model_kwargs is not None
        ):
            raise ValueError(
                "Either specify `create_model_kwargs` or `register_model_kwargs`."
            )
        return self

    def build(self):
        """
        Builds the model step by resolving the package name, creating or registering
        the model as part of the ModelStep and returning the ModelStep object.

        Returns:
            ModelStep: The built model step.

        Raises:
            RuntimeError: If `step_args` cannot be instantiated.
        """
        model = resolve_package_name(self.model)(
            role=self.role,
            sagemaker_session=self.sagemaker_session,
            vpc_config={
                "SecurityGroupIds": self.security_group_ids,
                "Subnets": self.subnets,
            },
            **self.model_kwargs,
        )

        if self.create_model_kwargs is not None:
            step_args = model.create(**self.create_model_kwargs)
        elif self.register_model_kwargs is not None:
            step_args = model.register(**self.register_model_kwargs)
        else:
            raise RuntimeError("`step_args` cannot be instantiated.")

        return ModelStep(
            name=self.name,
            step_args=step_args,
            depends_on=self.depends_on,
            retry_policies=self.retry_policies,
            **self.kwargs,
        )


class NotebookJobStepModel(BaseStepModel):
    """
    Represents a step model for a SageMaker Notebook Job step.

    Attributes:
        notebook_job_kwargs (Dict[str, Any]): Additional keyword arguments for the
            notebook job step.
    """

    notebook_job_kwargs: Dict[str, Any]

    def build(self):
        """
        Builds and returns a NotebookJobStep instance based on the model.

        Returns:
            NotebookJobStep: The built notebook job step.
        """
        return NotebookJobStep(
            name=self.name,
            role=self.role,
            security_group_ids=self.security_group_ids,
            subnets=self.subnets,
            # TODO: Pass in `sagemaker_session` once it is fixed in the sagemaker-sdk.
            # `sagemaker_session` is currently not supported but users can still
            # use this step model to create a notebook step though not recommended to
            # use NotebookJobStep until `sagemaker_session` is supported.
            # sagemaker_session=self.sagemaker_session,
            depends_on=self.depends_on,
            retry_policies=self.retry_policies,
            **self.notebook_job_kwargs,
        )


class ProcessingStepModel(BaseStepModel):
    """
    Represents a step model for a SageMaker Processing step.

    Attributes:
        processor (Optional[str]): The processor to use for the step.
            Default is "sagemaker.processing:Processor".
        processor_kwargs (Dict[str, Any]): Keyword arguments to pass to the processor
            class constructor.
        step_kwargs (Dict[str, Any]): Keyword arguments to pass to the processor's run
            method.
        property_files (List[Any]): List of property files to include in the step.
            Default is None.
    """

    processor: Optional[str] = "sagemaker.processing:Processor"
    processor_kwargs: Dict[str, Any]
    step_kwargs: Dict[str, Any]
    property_files: Optional[List[Any]] = None

    def build(self):
        """
        Build and return a ProcessingStep object based on the attributes of the
            ProcessingStepModel.

        Returns:
            ProcessingStep: The built ProcessingStep object.
        """
        processor = resolve_package_name(self.processor)(
            role=self.role,
            sagemaker_session=self.sagemaker_session,
            network_config=NetworkConfig(
                security_group_ids=self.security_group_ids,
                subnets=self.subnets,
            ),
            **self.processor_kwargs,
        )

        return ProcessingStep(
            name=self.name,
            step_args=processor.run(**self.step_kwargs),
            property_files=self.property_files,
            cache_config=self.cache_config,
            retry_policies=self.retry_policies,
            depends_on=self.depends_on,
            **self.kwargs,
        )


class TrainingStepModel(BaseStepModel):
    """
    Represents a step model for a SageMaker Training step.

    Attributes:
        estimator (Optional[str]): The name of the estimator class to use.
            Defaults to "sagemaker.estimator:Estimator".
        estimator_kwargs (Dict[str, Any]): Keyword arguments to pass to the estimator
            class constructor.
        fit_kwargs (Dict[str, Any]): Keyword arguments to pass to the estimator's fit
            method.
    """

    estimator: Optional[str] = "sagemaker.estimator:Estimator"
    estimator_kwargs: Dict[str, Any]
    fit_kwargs: Dict[str, Any]

    def build(self):
        """
        Builds and returns a TrainingStep object based on the model's attributes.

        Returns:
            TrainingStep: The built TrainingStep object.
        """

        estimator = resolve_package_name(self.estimator)(
            role=self.role,
            sagemaker_session=self.sagemaker_session,
            security_group_ids=self.security_group_ids,
            subnets=self.subnets,
            **self.estimator_kwargs,
        )

        return TrainingStep(
            name=self.name,
            step_args=estimator.fit(**self.fit_kwargs),
            cache_config=self.cache_config,
            retry_policies=self.retry_policies,
            depends_on=self.depends_on,
            **self.kwargs,
        )


class TransformStepModel(BaseStepModel):
    """
    Represents a step model for a SageMaker Transform step.

    Attributes:
        transformer (Optional[str]): The name of the transformer class to use.
            Defaults to "sagemaker.transformer:Transformer".
        transformer_kwargs (Dict[str, Any]): Keyword arguments to be passed to the
            transformer class constructor.
        step_kwargs (Dict[str, Any]): Keyword arguments to be passed to the
            transformer's transform method.
    """

    transformer: Optional[str] = "sagemaker.transformer:Transformer"
    transformer_kwargs: Dict[str, Any]
    step_kwargs: Dict[str, Any]

    def build(self):
        """
        Builds and returns a TransformStep object.

        Returns:
            TransformStep: The built TransformStep object.
        """
        transformer = resolve_package_name(self.transformer)(
            sagemaker_session=self.sagemaker_session,
            **self.transformer_kwargs,
        )

        return TransformStep(
            name=self.name,
            step_args=transformer.transform(**self.step_kwargs),
            cache_config=self.cache_config,
            retry_policies=self.retry_policies,
            depends_on=self.depends_on,
            **self.kwargs,
        )


class TuningStepModel(TrainingStepModel):
    """
    Represents a step model for a SageMaker Tuning step.

    Attributes:
        tuner (Optional[str]): The tuner to be used for hyperparameter tuning.
            Defaults to "sagemaker.tuner:HyperparameterTuner".
        tuner_kwargs (Dict[str, Any]): Additional keyword arguments to be passed to the
            tuner class constructor.

    Methods:
        build(): Builds and returns a TuningStep object based on the model configuration.
    """

    tuner: Optional[str] = "sagemaker.tuner:HyperparameterTuner"
    tuner_kwargs: Dict[str, Any]

    def build(self):
        """
        Builds and returns a TuningStep object based on the model configuration.

        Returns:
            TuningStep: The built TuningStep object.
        """
        estimator = resolve_package_name(self.estimator)(
            role=self.role,
            sagemaker_session=self.sagemaker_session,
            security_group_ids=self.security_group_ids,
            subnets=self.subnets,
            **self.estimator_kwargs,
        )

        tuner = resolve_package_name(self.tuner)(
            estimator=estimator, **self.tuner_kwargs
        )

        return TuningStep(
            name=self.name,
            step_args=tuner.fit(**self.fit_kwargs),
            cache_config=self.cache_config,
            retry_policies=self.retry_policies,
            depends_on=self.depends_on,
            **self.kwargs,
        )


def get_discriminator_value(v: Dict[str, Any]) -> str:
    """
    Returns the discriminator value based on the provided dictionary.

    Args:
        v (Dict[str, Any]): The dictionary containing the step configuration.

    Returns:
        str: The discriminator value.

    Raises:
        ValueError: If more than one step type is provided or if the required step types
            are not provided.
    """
    step_types = {
        "automl_kwargs",  # AutoML Step
        "check_job_config_kwargs",  # Clarify Check Step or Quality Check Step
        "conditions",  # Condition Step
        "emr_step_config_kwargs",  # EMR Step
        "error_message",  # Fail Step
        "estimator_kwargs",  # Train Step
        "lambda_func_kwargs",  # Lambda Step
        "model_kwargs",  # Model Step to create or register model
        "notebook_job_kwargs",  # Notebook Step
        "processor_kwargs",  # Processor Step
        "sqs_queue_url",  # Callback Step
        "transformer_kwargs",  # Transform step
        "tuner_kwargs",  # Hyperparameter Tuner Step
    }

    matched_keys = step_types & v.keys()

    match matched_keys:
        case matched_key if len(matched_key) == 1:
            return next(iter(matched_key))
        case _ if len(matched_key) == 2 and {
            "estimator_kwargs",
            "tuner_kwargs",
        }.issubset(matched_key):
            return "tuner_kwargs"
        case _:
            raise ValueError(
                f"Only one of {step_types} must be provided.\n"
                "Except for:\n"
                "\t* Hyperparameter Step: estimator_kwargs and tuner_kwargs "
                "must be provided at the minimum.\n"
            )


class StepModel(BaseModel):
    """A class that defines and builds SageMaker Pipeline Steps.

    Attributes:
        step (Union[AutoMLStepModel, CallbackStepModel, ProcessingStepModel,
            TrainingStepModel, TuningStepModel, TransformStepModel, ModelStepModel,
            CheckStepStepModel, ConditionStepModel, EMRStepModel, FailStepModel,
            LambdaStepModel, NotebookJobStepModel]):    The step to be built.

    """

    step: Annotated[
        Union[
            Annotated[AutoMLStepModel, Tag("automl_kwargs")],
            Annotated[CallbackStepModel, Tag("sqs_queue_url")],
            Annotated[ProcessingStepModel, Tag("processor_kwargs")],
            Annotated[TrainingStepModel, Tag("estimator_kwargs")],
            Annotated[TuningStepModel, Tag("tuner_kwargs")],
            Annotated[TransformStepModel, Tag("transformer_kwargs")],
            Annotated[ModelStepModel, Tag("model_kwargs")],
            Annotated[CheckStepStepModel, Tag("check_job_config_kwargs")],
            Annotated[ConditionStepModel, Tag("conditions")],
            Annotated[EMRStepModel, Tag("emr_step_config_kwargs")],
            Annotated[FailStepModel, Tag("error_message")],
            Annotated[LambdaStepModel, Tag("lambda_func_kwargs")],
            Annotated[NotebookJobStepModel, Tag("notebook_job_kwargs")],
        ],
        Discriminator(get_discriminator_value),
    ]

    def build(self):
        """Builds the step.

        Returns:
            The built step.

        """
        try:
            return self.step.build()
        except Exception as err:
            raise SagemakerStepException(
                f"Error when building step: {self.step.name}.\nError: {err}"
            ) from err
