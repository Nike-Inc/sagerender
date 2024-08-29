# Copyright 2024-present, Nike, Inc.
# All rights reserved.
#
# This source code is licensed under the Apache-2.0 license found in
# the LICENSE file in the root directory of this source tree.


import math
import unittest
from importlib.metadata import EntryPoint
from unittest import mock

from sagerender.utilities.mixin import ResourceLocatorMixin


class ExampleResourceLocator(ResourceLocatorMixin):
    @property
    def entry_point_group(self):
        return "some.namespace.group"


class MockEntryPoint(object):
    def __init__(self, entry_point):
        self.entry_point = entry_point

    @property
    def name(self):
        return self.entry_point.name

    def load(self):
        return self.entry_point.load()


class TestEntryPoints(unittest.TestCase):
    @mock.patch("sagerender.utilities.mixin.entry_points")
    def test_resource_locator_mixin(self, mock_iter_entry_points):
        entry_point = EntryPoint(
            name="example1",
            value="math:sqrt",
            group="some.namespace.group",
        )
        mock_entry_point = MockEntryPoint(entry_point)
        mock_iter_entry_points.return_value = [mock_entry_point]
        locator = ExampleResourceLocator()
        resource = locator.get_resource("example1")
        with self.assertRaises(KeyError):
            locator.get_resource("bad")
        self.assertEqual(math.sqrt, resource)
        (mock_iter_entry_points.assert_called_once_with(group="some.namespace.group"))
        self.assertSetEqual({"example1"}, set(locator.get_resource_names()))


if __name__ == "__main__":
    unittest.main()
