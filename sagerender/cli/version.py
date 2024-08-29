# Copyright 2024-present, Nike, Inc.
# All rights reserved.
#
# This source code is licensed under the Apache-2.0 license found in
# the LICENSE file in the root directory of this source tree.

import sys

from sagerender import __version__


def main(argv=None):
    print(f"sagerender {__version__}")


if __name__ == "__main__":
    sys.exit(main())
