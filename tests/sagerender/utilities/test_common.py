# Copyright 2024-present, Nike, Inc.
# All rights reserved.
#
# This source code is licensed under the Apache-2.0 license found in
# the LICENSE file in the root directory of this source tree.

import os
import unittest
from math import sqrt
from unittest import mock

import yaml
from cerberus.client import CerberusClientException
from parameterized import parameterized
from sagemaker.processing import Processor
from sagerender.utilities.common import (
    env_vars_constructor,
    get_resource_config,
    get_secret_from_cerberus,
    resolve_enum_name,
    resolve_package_name,
)

_HOST = "https://example.cerberus.com"


def get_secret_from_cerberus_side_effect(secret_path, host):
    if host != _HOST:
        raise ValueError(f"Expected host value: {_HOST} but found {host}")
    data = {
        "app/path/team_info": {
            "aws_region": "us-west-2",
            "team_exec_role": "aws:arn:iam::123456789:role/execution-role",
        },
        "app/path/network": {
            "security_group_id": "sg-123456789",
            "private_subnet_ids": "subnet-123,subnet-456,subnet-789",
        },
    }
    return data[secret_path]


class MockCerberusClient(object):
    def __init__(self, host):
        self.host = host
        self.data = {
            "app/test_sdb/test_secure_data": {
                "username": "celect",
                "password": "password",
            },
            "app/test_sdb/data": {"token": "tokenizer"},
        }

    def get_secrets_data(self, path):
        try:
            return self.data[path]
        except KeyError as err:
            raise CerberusClientException from err


class TestUtilitiesCommon(unittest.TestCase):
    @parameterized.expand(
        [
            ("data: no-replace", "data: no-replace"),
            ("data: ${ENV_VAR_1}", "data: ENV_VALUE_1"),
            ("data: ${ENV_VAR_1}/${ENV_VAR_2}", "data: ENV_VALUE_1/ENV_VALUE_2"),
            ("data: ${ENV_VAR_3}", "data: ENV_VAR_3"),
        ]
    )
    @mock.patch.dict(
        os.environ,
        {
            "ENV_VAR_1": "ENV_VALUE_1",
            "ENV_VAR_2": "ENV_VALUE_2",
        },
    )
    def test_env_vars_constructor(self, test_input, expected):
        actual = env_vars_constructor(
            loader=yaml.SafeLoader(test_input),
            node=yaml.nodes.ScalarNode(tag="!env", value=test_input),
        )
        self.assertEqual(actual, expected)

    @mock.patch("sagerender.utilities.common.CerberusClient")
    def test_get_secret_from_cerberus(self, mock_cerberus_client):
        mock_cerberus_client.return_value = MockCerberusClient(host=_HOST)

        actual = get_secret_from_cerberus("app/test_sdb/test_secure_data", _HOST)

        self.assertEqual(
            actual,
            {
                "username": "celect",
                "password": "password",
            },
        )
        mock_cerberus_client.assert_called_once_with(_HOST)

        with self.assertRaises(CerberusClientException):
            _ = get_secret_from_cerberus("app/non-existent/test-key", _HOST)

    @mock.patch("sagerender.utilities.common.get_secret_from_cerberus")
    def test_get_resource_config(self, mock_get_secret_from_cerberus):
        _host = "https://example.cerberus.com"

        mock_get_secret_from_cerberus.side_effect = get_secret_from_cerberus_side_effect

        expected = {
            "region": "us-west-2",
            "execution_role": "aws:arn:iam::123456789:role/execution-role",
            "security_group_ids": ["sg-123456789"],
            "subnets": ["subnet-123", "subnet-456", "subnet-789"],
        }

        cerberus_cfg = {
            "host": _host,
            "sdb": {
                "team": "app/path/team_info",
                "network": "app/path/network",
            },
        }

        actual = get_resource_config(cerberus_cfg=cerberus_cfg)

        self.assertDictEqual(expected, actual)

        actual = get_resource_config(cerberus_cfg=None)
        self.assertIsNone(actual)

    def test_resolve_enum_name(self):
        from sagemaker.workflow.retry import StepExceptionTypeEnum

        self.assertEqual(
            StepExceptionTypeEnum.THROTTLING,
            resolve_enum_name(
                "sagemaker.workflow.retry:StepExceptionTypeEnum:THROTTLING"
            ),
        )

    def test_resolve_package_name(self):
        self.assertEqual(sqrt, resolve_package_name("math:sqrt"))
        self.assertEqual(
            Processor, resolve_package_name("sagemaker.processing:Processor")
        )


if __name__ == "__main__":
    unittest.main()
