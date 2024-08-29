# Copyright 2024-present, Nike, Inc.
# All rights reserved.
#
# This source code is licensed under the Apache-2.0 license found in
# the LICENSE file in the root directory of this source tree.

"""Module for managing the SageRender Command Line Interface (CLI).

This module provides the SageRenderCLI class, which is used to handle command line
interactions for the SageRender tool. The CLI supports various commands such as
`upsert-pipeline` and `run-pipeline` for managing SageMaker pipelines.

The SageRenderCLI class uses the argparse library to parse command line arguments,
and it leverages the ResourceLocatorMixin for locating and loading command resources.

The module also includes a main function that serves as the entry point for the CLI.
"""

import argparse
import sys

from sagerender.utilities.mixin import ResourceLocatorMixin


class SageRenderCLI(ResourceLocatorMixin):
    @property
    def entry_point_group(self):
        return "sagerender.cli.command"

    @property
    def usage(self):
        _usage = [
            "sagerender <command> [<args>]",
            "The most commonly used SageRender commands are:",
        ]

        description = {
            "upsert-pipeline": "Configure and Upsert SageMaker Pipeline",
            "version": "Version of SageRender",
            "run-pipeline": "Run SageMaker Pipeline",
        }

        for key in sorted(self.get_resource_names()):
            try:
                _usage.append(
                    "{command}\t\t{description}".format(
                        command=key, description=description[key]
                    )
                )
            except KeyError as err:
                raise RuntimeError("Missing description for %s" % key) from err

        return "\n".join(_usage)

    def __init__(self):
        parser = argparse.ArgumentParser(description="SageRender CLI", usage=self.usage)
        parser.add_argument(
            "command",
            choices=self.get_resource_names(),
            help="Subcommand to run",
            metavar="COMMAND",
        )
        # parse_args defaults to [1:] for args, but you need to
        # exclude the rest of the args too, or validation will fail
        args = parser.parse_args(sys.argv[1:2])
        command = self.get_resource(args.command)
        command(sys.argv[2:])


def main():
    SageRenderCLI()
