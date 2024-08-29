# Copyright 2024-present, Nike, Inc.
# All rights reserved.
#
# This source code is licensed under the Apache-2.0 license found in
# the LICENSE file in the root directory of this source tree.

"""Module for managing AWS SageMaker Pipeline Blueprints.

This module provides the PipelineBlueprint class, which is used to create and manage
pipeline blueprints using Phiera. A pipeline blueprint is a template that defines the
structure of a SageMaker pipeline, including the steps involved and their order.

The PipelineBlueprint class supports setting and getting various properties of the
blueprint, such as its filename, configuration, and context. It also includes methods
for validating the blueprint and setting its context.

This module uses the Singleton design pattern for the PipelineBlueprint class, ensuring
that only one instance of the class exists at any given time.
"""

import os
from typing import Dict, List

import yaml
from multipledispatch import dispatch
from phiera import Hiera

from sagerender.defaults import HIERA_FILE, PATTERN_ENV_VARS, SAGERENDER_HIERA_FILE
from sagerender.exceptions import PipelineBlueprintValidationError
from sagerender.utilities.common import env_vars_constructor


class PipelineBlueprint:
    """
    A class to create pipeline blueprint using Phiera.
    """

    instance = None

    def __new__(cls):
        if not cls.instance:
            cls.instance = super(PipelineBlueprint, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        self.filename = os.getenv(SAGERENDER_HIERA_FILE, default=HIERA_FILE)
        self.config = self.filename
        self.context = {}
        self.blueprint = None
        self.validate()

    @property
    def filename(self):
        return self._filename

    @filename.setter
    def filename(self, filename: str):
        self._filename = filename

    @property
    def config(self) -> Dict:
        return self._config

    @config.setter
    def config(self, filename: str):
        with open(filename, "rb") as file_obj:
            self._config = yaml.safe_load(file_obj)

    @property
    def hiera_context(self) -> List:
        return self._config["context"]

    @dispatch(dict)
    def set_context(self, context: Dict):
        self.context.update(context)

    @dispatch(str, str)
    def set_context(self, key: str, value: str):
        self.context[key] = value

    def create(self):
        self.blueprint = Hiera(
            self.config,
            context=self.context,
            base_path=os.path.dirname(self.filename),
        )

    def get_definition(self, key: str, throw_error_on_missing_key: bool = True):
        return self.blueprint.get(
            key=key,
            merge=dict,
            merge_deep=True,
            throw=throw_error_on_missing_key,
            # Additional arguments can be replaced using context param, in the YAML,
            # these are referenced using the key. For ex, %{argument_name}
            context=self.context,
        )

    def validate(self):
        hiera_keys = ["backends", "context", "hierarchy"]

        # Validate required keys in the hiera configuration file
        for key in hiera_keys:
            try:
                assert isinstance(
                    self.config[key], list
                ), f"{key} must be of type list, found: {type(self.config[key])}"
            except KeyError as err:
                raise PipelineBlueprintValidationError(
                    f"{key} not defined in the hiera configuration file: "
                    f"{self.filename}"
                ) from err
            except AssertionError as err:
                raise PipelineBlueprintValidationError(err) from err

        # Validate datadir is defined for the backends
        for backend in self.config["backends"]:
            try:
                assert isinstance(self.config[backend], dict), (
                    f"{backend} must be of type dict, "
                    f"found: {type(self.config[backend])}"
                )
                assert (
                    "datadir" in self.config[backend]
                ), f"datadir not found in {backend} configuration"
            except KeyError as err:
                raise PipelineBlueprintValidationError(
                    f"{backend} backend not defined in the hiera configuration file:"
                    f"{self.filename}"
                ) from err
            except AssertionError as err:
                raise PipelineBlueprintValidationError(err) from err


# PyYaml Loaders to work with Phiera
yaml.Loader.add_implicit_resolver("!env", PATTERN_ENV_VARS, None)
yaml.Loader.add_constructor("!env", env_vars_constructor)
