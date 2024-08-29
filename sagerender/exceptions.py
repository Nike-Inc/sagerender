# Copyright 2024-present, Nike, Inc.
# All rights reserved.
#
# This source code is licensed under the Apache-2.0 license found in
# the LICENSE file in the root directory of this source tree.

"""Module for defining custom exceptions for the SageRender tool.

This module provides several custom exception classes that are used throughout
the SageRender tool to handle various error conditions. These exceptions include:

- SagemakerPipelineException: A general exception for errors related to SageMaker
Pipelines.
- SageRenderPipelineBlueprintError: A base exception for errors related to SageRender
Pipeline Blueprints.
- PipelineBlueprintValidationError: Thrown when there are validation errors in a
pipeline blueprint.
- SageRenderPipelineBuilderError: A base exception for errors related to the SageRender
Pipeline Builder.
- PipelineNotFoundError: Thrown when a pipeline definition is missing in the
PipelineBuilder.

Each exception class is derived from the built-in Python Exception class.
"""


class SagemakerPipelineException(Exception):
    pass


class SagemakerStepException(Exception):
    """Thrown in case of errors during SageMaker step build"""


class SageRenderPipelineBlueprintError(Exception):
    """Base class for all SageRender Pipeline Blueprint Exceptions"""


class PipelineBlueprintValidationError(SageRenderPipelineBlueprintError):
    """Thrown in case of validation errors in pipeline blueprint"""


class SageRenderPipelineBuilderError(Exception):
    """Base class for SageRender Pipeline Builder Exceptions"""


class PipelineNotFoundError(SageRenderPipelineBuilderError):
    """Thrown in case of missing pipeline definition in PipelineBuilder"""
