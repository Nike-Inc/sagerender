# Copyright 2024-present, Nike, Inc.
# All rights reserved.
#
# This source code is licensed under the Apache-2.0 license found in
# the LICENSE file in the root directory of this source tree.

"""Module for defining default constants for the SageRender tool.

This module defines several constants that are used as default values or identifiers
across the SageRender tool. These include:

- CERBERUS: The name of the validation library used by SageRender.
- HIERA_FILE: The default filename for the Hiera configuration file.
- PIPELINE_PARAMETERS: The default identifier for pipeline parameters.
- SAGERENDER_HIERA_FILE: The environment variable name for specifying a custom Hiera
    configuration file.
- TAGS: The default identifier for tags.
- PROCESSING: The default identifier for processing steps.

These constants help maintain consistency and readability across the SageRender codebase.
"""

import re

CERBERUS = "cerberus"
HIERA_FILE = "hiera.yaml"
PATTERN_ENV_VARS = re.compile(r".*?\${(.*?)}.*?")
PIPELINE_EXPERIMENT_CONFIG = "pipeline_experiment_config"
PIPELINE_PARAMETERS = "parameters"
PIPELINE_SESSION_BUCKET = "session_bucket"
PIPELINE_PROPERTY_FILES = "property_files"
SAGERENDER_HIERA_FILE = "SAGERENDER_HIERA_FILE"
TAGS = "tags"
PROCESSING = "PROCESSING"
EXECUTION_VARIABLES_CLASS_PATH = (
    "sagemaker.workflow.execution_variables:ExecutionVariables"
)
EXECUTION_VARIABLE_PREFIX = "exec:"
FACTORY_ENUM = "factory_enum"
FACTORY_FUNCTION = "factory_function"
PARAMETER_PREFIX = "param:"
PROPERTY_FILE_PREFIX = "propertyFile:"
PROPERTIES_IDENTIFIER = ".properties."
RESERVED_STEP_KEYWORDS = {"role", "sagemaker_session", "security_group_ids", "subnets"}
RESOURCE_CONFIG = "resource_config"
