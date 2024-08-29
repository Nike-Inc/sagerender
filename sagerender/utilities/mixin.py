# Copyright 2024-present, Nike, Inc.
# All rights reserved.
#
# This source code is licensed under the Apache-2.0 license found in
# the LICENSE file in the root directory of this source tree.

import logging
from abc import ABCMeta
from importlib.metadata import entry_points

logger = logging.getLogger(__name__)


# noinspection PyAttributeOutsideInit
class ResourceLocatorMixin(metaclass=ABCMeta):
    @property
    def entry_point_group(self):
        return

    def register_resources(self):
        if self.registered_resources:
            logger.warning(
                "Resources already registered. "
                "Registering again will override "
                "existing resources"
            )
        self.__resources = {}
        for entry_point in entry_points(group=self.entry_point_group):
            self.__resources[entry_point.name] = entry_point.load()

    @property
    def registered_resources(self):
        try:
            return isinstance(self.__resources, dict)
        except AttributeError:
            return False

    def lazy_register_resources(self):
        if not self.registered_resources:
            self.register_resources()

    def get_resource(self, name):
        self.lazy_register_resources()
        return self.__resources[name]

    def get_resource_names(self):
        self.lazy_register_resources()
        return self.__resources.keys()
