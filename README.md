# WESnake

A GA4GH compliant Workflow-Execution-Service (WES) for Snakemake.

## Installation

```bash
conda env create -n wesnake -f environment.yaml
conda activate wesnake
```

## Tests

Tests use [testcontainers-python](https://testcontainers-python.readthedocs.io/en/latest/database.html) > 2.6.

Currently, this is available only on the master branch of the testcontainers-python repository.

To set the environment correctly up you need to first install the conda environment like described above. After that install the development head of testcontainers-python as follows

```bash
conda activate wesnake
git clone https://github.com/testcontainers/testcontainers-python.git
cd testcontainers-python
python3 setup.py build
pip install ./
```

