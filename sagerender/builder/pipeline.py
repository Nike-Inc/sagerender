# Copyright 2024-present, Nike, Inc.
# All rights reserved.
#
# This source code is licensed under the Apache-2.0 license found in
# the LICENSE file in the root directory of this source tree.

"""Module for building and managing AWS SageMaker Pipelines.

This module provides functionality for creating SageMaker Pipelines, adding steps to the
pipeline, setting pipeline parameters, and managing the pipeline lifecycle. It includes
support for various step types like processing steps, training steps, and model
deployment steps.

"""

from typing import Dict, Union

from sagemaker.workflow.execution_variables import ExecutionVariables
from sagemaker.workflow.functions import Join, JsonGet
from sagemaker.workflow.parallelism_config import ParallelismConfiguration
from sagemaker.workflow.pipeline import (
    Pipeline,
    PipelineDefinitionConfig,
    PipelineExperimentConfig,
)
from sagemaker.workflow.properties import PropertyFile

from sagerender.builder.step import StepModel
from sagerender.defaults import (
    EXECUTION_VARIABLE_PREFIX,
    EXECUTION_VARIABLES_CLASS_PATH,
    FACTORY_ENUM,
    FACTORY_FUNCTION,
    PARAMETER_PREFIX,
    PROPERTIES_IDENTIFIER,
    PROPERTY_FILE_PREFIX,
)
from sagerender.exceptions import PipelineNotFoundError
from sagerender.utilities.common import resolve_enum_name, resolve_package_name


class PipelineBuilder:
    """A class to build and upsert SageMaker Pipeline Definition"""

    def __init__(self):
        self.name = None
        self.security_group_ids = []
        self.subnets = []
        self.parameters = {}
        self.property_files = {}
        self.pipeline = None
        self.role_arn = None
        self.sagemaker_session = None
        self.max_parallel_execution_steps = None
        self.steps = {}
        self.tags = []
        self.use_custom_job_prefix = False
        self.pipeline_experiment_config = PipelineExperimentConfig(
            ExecutionVariables.PIPELINE_NAME, ExecutionVariables.PIPELINE_EXECUTION_ID
        )

    def add_parameter(self, parameter: str, value: Dict):
        self.parameters[parameter] = resolve_package_name(value["type"])(
            name=parameter, default_value=value.get("default_value")
        )
        return self

    def add_parameters(self, parameters: Dict[str, Dict]):
        for parameter, value in parameters.items():
            self.add_parameter(parameter, value)
        return self

    def add_property_file(self, property_file: str, kwargs: Dict):
        """

        Args:
            property_file (str): Name of the property file
            kwargs (Dict): Keyword arguments to create an instance of the `PropertyFile`

        Returns:
            An instance of the `PipelineBuilder` class.
        """
        self.property_files[property_file] = PropertyFile(name=property_file, **kwargs)
        return self

    def add_property_files(self, property_files: Dict[str, Dict]):
        """

        Args:
            property_files (Dict[str, Dict]): A dictionary containing the property files
                configuration for the pipeline

        Returns:
            An instance of the `PipelineBuilder` class.
        """
        for property_file, kwargs in property_files.items():
            self.add_property_file(property_file, kwargs)
        return self

    def _replace_argument(self, argument: str):
        """Replace the specified argument with a SageMaker PrimitiveType
        For parameters and property files, lookup from internal resolved objects
        if it exists, else return the argument.
        For execution variables, instantiate the execution variable object.
        For properties, return the step properties reference object.

        i.e.
            `param:parameter` -> sagemaker.workflow.parameters.Parameter
            `exec:exec_name` -> sagemaker.workflow.execution_variables.ExecutionVariable
            `propertyFile:name` ->  sagemaker.workflow.properties.PropertyFile
            `step_name.properties.<path>` -> sagemaker.workflow.properties.Properties

        :param argument: The argument in which to replace
        :return: The updated argument value, or the passed in argument
        """

        if isinstance(argument, str):
            match argument:
                case arg if arg.startswith(PARAMETER_PREFIX):
                    return self.parameters[argument.split(":")[1]]
                case arg if arg.startswith(EXECUTION_VARIABLE_PREFIX):
                    return resolve_enum_name(
                        f"{EXECUTION_VARIABLES_CLASS_PATH}:{argument.split(':')[1]}"
                    )
                case arg if arg.startswith(PROPERTY_FILE_PREFIX):
                    return self.property_files[argument.split(":")[1]]
                case arg if PROPERTIES_IDENTIFIER in arg:
                    step_name = argument.split(PROPERTIES_IDENTIFIER)[0]
                    return eval(
                        argument.replace(step_name, f'self.steps["{step_name}"]')
                    )

        return argument

    def _replace_factory_function(self, factory_function, kwargs):
        """
        Resolve and return an instance of the factory function defined.

        Args:
            factory_function (str): Name of the function
            kwargs (dict): keyword arguments to the function
        """
        return resolve_package_name(factory_function)(
            **self._replace_step_arguments(kwargs)
        )

    def _replace_step_arguments(self, arguments: dict) -> Union[dict, Join, JsonGet]:
        """Recursively iterate over a dictionary of arguments and replace the
        values with SageMaker Primitive Types or Functions.

        :param arguments: Dictionary of arguments to iterate over
        :return: dict of completed replacements
        """
        for key in arguments.keys():
            if key == FACTORY_FUNCTION:
                return self._replace_factory_function(**arguments)
            elif key == FACTORY_ENUM:
                return resolve_enum_name(arguments[key])
            elif isinstance(arguments[key], dict):
                arguments[key] = self._replace_step_arguments(arguments[key])
            elif isinstance(arguments[key], list):
                for idx, argument in enumerate(arguments[key]):
                    if isinstance(argument, dict):
                        arguments[key][idx] = self._replace_step_arguments(argument)
                    else:
                        arguments[key][idx] = self._replace_argument(argument)
            elif isinstance(arguments[key], str):
                arguments[key] = self._replace_argument(arguments[key])

        return arguments

    def _replace_with_step_collection(self, steps_collection):
        return [self.steps.pop(step_name) for step_name in steps_collection]

    def add_step(self, name: str, kwargs: Dict):
        kwargs = self._replace_step_arguments(kwargs)

        kwargs.update(
            {
                "name": kwargs.get("name", name),
                "role": self.role_arn,
                "sagemaker_session": self.sagemaker_session,
                "security_group_ids": self.security_group_ids,
                "subnets": self.subnets,
            }
        )

        # This is required only for condition step as it expects step object
        if "if_steps" in kwargs:
            kwargs["if_steps"] = self._replace_with_step_collection(kwargs["if_steps"])

        if "else_steps" in kwargs:
            kwargs["else_steps"] = self._replace_with_step_collection(
                kwargs["else_steps"]
            )

        step = StepModel.model_validate({"step": kwargs}).build()
        self.steps[step.name] = step

    def add_steps(self, steps: Dict):
        for name, kwargs in steps.items():
            if name in [
                "name",
                "parameters",
                "max_parallel_execution_steps",
                "property_files",
                "use_custom_job_prefix",
                "pipeline_experiment_config",
            ]:
                continue
            self.add_step(name, kwargs)
        return self

    def add_tag(self, tag):
        self.tags.append(tag)
        return self

    def add_tags(self, tags):
        for tag in tags:
            self.add_tag(tag)
        return self

    def set_name(self, name: str):
        self.name = name
        return self

    def add_security_group_id(self, security_group_id):
        self.security_group_ids.append(security_group_id)
        return self

    def add_security_group_ids(self, security_group_ids):
        for security_group_id in security_group_ids:
            self.add_security_group_id(security_group_id)

        return self

    def add_subnet(self, subnet):
        self.subnets.append(subnet)
        return self

    def add_subnets(self, subnets):
        for subnet in subnets:
            self.add_subnet(subnet)
        return self

    def set_role_arn(self, role_arn: str):
        self.role_arn = role_arn
        return self

    def set_sagemaker_session(self, sagemaker_session):
        self.sagemaker_session = sagemaker_session
        return self

    def set_max_parallel_execution_steps(self, max_parallel_execution_steps: int):
        """

        Args:
            max_parallel_execution_steps (int): Maximum number of pipeline steps to run
                in parallel.

        Returns:
            An instance of the `PipelineBuilder` class.
        """
        self.max_parallel_execution_steps = max_parallel_execution_steps
        return self

    def set_use_custom_job_prefix(self, use_custom_job_prefix):
        self.use_custom_job_prefix = use_custom_job_prefix
        return self

    def set_pipeline_experiment_config(self, pipeline_experiment_config):
        self.pipeline_experiment_config = (
            PipelineExperimentConfig(
                **self._replace_step_arguments(pipeline_experiment_config)
            )
            if pipeline_experiment_config is not None
            else self.pipeline_experiment_config
        )
        return self

    @property
    def parallelism_config(self):
        return (
            ParallelismConfiguration(
                max_parallel_execution_steps=self.max_parallel_execution_steps
            )
            if self.max_parallel_execution_steps is not None
            else self.max_parallel_execution_steps
        )

    @property
    def pipeline_definition_config(self):
        return PipelineDefinitionConfig(use_custom_job_prefix=self.use_custom_job_prefix)

    def build(self):
        self.pipeline = Pipeline(
            name=self.name,
            parameters=list(self.parameters.values()),
            steps=list(self.steps.values()),
            sagemaker_session=self.sagemaker_session,
            pipeline_definition_config=self.pipeline_definition_config,
            pipeline_experiment_config=self.pipeline_experiment_config,
        )

        return self

    def definition(self):
        if not self.pipeline:
            raise PipelineNotFoundError(f"Pipeline definition not found for {self.name}")
        return self.pipeline.definition()

    def upsert(self):
        if not self.pipeline:
            raise PipelineNotFoundError(f"Pipeline definition not found for {self.name}")
        self.pipeline.upsert(
            role_arn=self.role_arn,
            tags=self.tags,
            parallelism_config=self.parallelism_config,
        )

    def run(self, parameters=None):
        if not self.pipeline:
            raise PipelineNotFoundError(f"Pipeline definition not found for {self.name}")
        self.pipeline.start(parameters=parameters)
