# WESnake

A GA4GH compliant Workflow-Execution-Service (WES) for Snakemake.

## Tests

Tests use [testcontainers-python](https://testcontainers-python.readthedocs.io/en/latest/database.html) > 2.6.

Currently, this is available only on the master branch of the testcontainers-python repository.

To set the environment correctly up you need to first install the conda environment like described above. After that install the development head of testcontainers-python as follows

```bash
conda activate wesnake
pip install git+https://github.com/testcontainers/testcontainers-python.git
```

## Installation from sources

```bash
cd wesnake
python setup.py install
```

## Configuration

Please adapt the `config.yaml` file.

## Running

An executable called `wesnake` is installed. Run it with

```bash
wesnake --config config.yaml
```

