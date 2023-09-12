#!/usr/bin/env python

# SPDX-FileCopyrightText: 2023 The WESkit Team
#
# SPDX-License-Identifier: MIT

from setuptools import setup, find_packages

setup(name='WESkit',
      packages=find_packages(),
      version='0.0.1',
      entry_points={
            "console_scripts": [
                  "weskit = weskit.__main__:main"
            ]
      },
      include_package_data=True
      )
