# WESnake

A GA4GH compliant Workflow-Execution-Service (WES) for Snakemake.

## Installation from sources

Install a Conda environment as follows

```bash
conda env create -n wesnake -f environment.yaml
conda activate wesnake
```

Then install the application

```bash
git clone https://gitlab.com/one-touch-pipeline/wesnake.git
cd wesnake
python setup.py install
```

By this, an executable called `wesnake` is installed.

## Tests

Tests use [testcontainers-python](https://testcontainers-python.readthedocs.io/en/latest/database.html) > 2.6.

Currently, this is available only on the master branch of the testcontainers-python repository.

To set the environment correctly up you need to first install the conda environment like described above. After that install the development head of testcontainers-python as follows

```bash
conda activate wesnake
pip install git+https://github.com/testcontainers/testcontainers-python.git
```

To run the tests

```bash
python -m pytest
```

## Configuration

Please adapt the `config.yaml` file.

## Running

Run it with

```bash
wesnake --config config.yaml
```