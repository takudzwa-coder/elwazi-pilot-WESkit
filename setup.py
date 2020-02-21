#!/usr/bin/env python

from distutils.core import setup
setup(name='WESnake',
      version='0.1',
      description="A Workflow Execution Service (GA4GH) for Snakemake",
      url="https://gitlab.com/one-touch-pipeline/wesnake",
      packages=["ga4gh"],
      license="MIT",    # TODO: What licence do we want?
      )