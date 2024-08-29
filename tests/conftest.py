# Copyright 2024-present, Nike, Inc.
# All rights reserved.
#
# This source code is licensed under the Apache-2.0 license found in
# the LICENSE file in the root directory of this source tree.

import os

import pytest


@pytest.fixture()
def reset_environment():
    init_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(init_env)


@pytest.fixture(autouse=True)
def patch_default_region(reset_environment):
    os.environ["AWS_DEFAULT_REGION"] = "us-west-2"
    os.environ["AWS_REGION"] = "us-west-2"
