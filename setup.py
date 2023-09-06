#!/usr/bin/env python

# Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
# SPDX-FileCopyrightText: 2023 2023 The WESkit Team
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
