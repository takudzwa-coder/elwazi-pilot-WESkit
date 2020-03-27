#!/usr/bin/env python

from setuptools import setup, find_packages
setup(name='WESnake',
      packages=find_packages(),
      version='0.0.1',
      entry_points={
            "console_scripts": [
                  "wesnake = ga4gh.wes.wesnake:main"
            ]
      })