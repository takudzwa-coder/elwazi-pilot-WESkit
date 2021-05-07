#!/usr/bin/env python

#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

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
