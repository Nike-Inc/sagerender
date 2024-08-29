# Copyright 2024-present, Nike, Inc.
# All rights reserved.
#
# This source code is licensed under the Apache-2.0 license found in
# the LICENSE file in the root directory of this source tree.

"""Module for common utilities used across the SageRender tool.

This module provides various utility functions that are used in multiple places
across the SageRender tool. These include:

- resolve_enum_name: A function for resolving the name of an enum object from a string
  that includes the package name, class name, and enum name.

- setup_logger: A function for setting up the logging configuration for the SageRender
    tool. This includes setting the logging level and format based on environment
    variables or provided arguments.

These utilities are designed to be general-purpose and reusable, and they do not depend
on any specific features or components of the SageRender tool.
"""

import logging
import os
from importlib import import_module
from logging import Logger
from typing import Any, Dict, Union

from cerberus.client import CerberusClient, CerberusClientException

from sagerender.defaults import PATTERN_ENV_VARS


def get_secret_from_cerberus(secret_path: str, host: str):
    """

    Args:
        secret_path (str)   : Secure Data Path on Cerberus
        host (str)          : URL of the Cerberus Host

    Returns:
        secrets (dict)   : Python dictionary where key is the secret name and value is
            the secret
    """

    try:
        client = CerberusClient(host)
        secrets = client.get_secrets_data(secret_path)
    except CerberusClientException as e:
        raise e
    return secrets


def get_resource_config(cerberus_cfg: Union[dict, None]) -> Union[Dict, None]:
    """
    Setups configurations
    Args:
        cerberus_cfg (dict): Cerberus configuration for retrieving team-specific
            information
    """

    if cerberus_cfg is None:
        return None

    cerberus_team_secrets = get_secret_from_cerberus(
        secret_path=cerberus_cfg["sdb"]["team"],
        host=cerberus_cfg["host"],
    )

    cerberus_network_secrets = get_secret_from_cerberus(
        secret_path=cerberus_cfg["sdb"]["network"],
        host=cerberus_cfg["host"],
    )

    return {
        "region": cerberus_team_secrets["aws_region"],
        "execution_role": cerberus_team_secrets["team_exec_role"],
        "security_group_ids": cerberus_network_secrets["security_group_id"].split(","),
        "subnets": cerberus_network_secrets["private_subnet_ids"].split(","),
    }


def env_vars_constructor(loader: Any, node: Any) -> str:
    """
    YAML Constructor for resolving Environment Variables

    Args:
        loader (Any): YAML Loader class object
        node (Any): node matching the regex pattern for environment variables

    Returns:
        The node with values resolved by environment variables lookup or node itself if
        environment variables are not found
    """
    value = loader.construct_scalar(node)
    for group in PATTERN_ENV_VARS.findall(value):
        value = value.replace(f"${{{group}}}", os.environ.get(group, group))
    return value


def resolve_package_name(package_name: str):
    """
    Args:
        package_name (str): The expected format of package_name is 'package:name' where
        'package' should be an importable module name and 'name' should be the name of
        an object accessible within that module

    Returns:
        Object of the module looked up by name
    """
    # TODO: Add error handling

    package, name = package_name.split(":")
    module = import_module(package)
    return getattr(module, name)


def resolve_enum_name(enum_package_name: str):
    """
    Args:
        enum_package_name (str): The expected format for enum_package_name is
        'package:name:enum' where 'package' should be an importable module name and
        'name' should be the name of the enum class accessible within that module and
        'enum' is the name of the enum type available within the enum class.

    Returns:
        Enum Object of the module looked up by name
    """
    # TODO: Add error handling

    package_name, enum = enum_package_name.rsplit(sep=":", maxsplit=1)
    return getattr(resolve_package_name(package_name), enum)


def setup_logger(logger: Logger, verbose: bool = False):  # pragma: no cover
    """

    Args:
        logger (Logger): Instance of the logger.
        verbose (bool): If true, enable debug logging.

    Returns:

    """
    level = (
        logging.DEBUG
        if verbose
        else (os.environ.get("SAGERENDER_LOG_LEVEL", "INFO").upper())
    )
    format_ = os.environ.get(
        "SAGERENDER_LOG_FORMAT",
        "[%(asctime)s] [%(name)s] [%(processName)s] [%(levelname)s]: %(message)s",
    )

    log_handler = logging.StreamHandler()
    log_handler.setLevel(level)

    log_format = logging.Formatter(format_)
    log_handler.setFormatter(log_format)

    logger.addHandler(log_handler)
