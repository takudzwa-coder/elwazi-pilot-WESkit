#!/usr/bin/env python

from setuptools import setup, find_packages
setup(name='WESnake',
      packages=find_packages(),
      version='0.0.1',
      entry_points={
            "console_scripts": [
                  "wesnake = wesnake.wesnake:main"
            ]
      },
      data_files=[("config", ["wesnake/config/validation.yaml", "wesnake/config/log-config.yaml"])]
      )