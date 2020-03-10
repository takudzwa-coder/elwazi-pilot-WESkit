# WESnake

A GA4GH compliant Workflow-Execution-Service (WES) for Snakemake.

## Tests

Tests use [testcontainers-python](https://testcontainers-python.readthedocs.io/en/latest/database.html) > 2.6.

To set the environment correctly up you need to first install the conda environment like described above. After that install the development head of testcontainers-python as follows

```bash
conda activate wesnake
pip install testcontainers[mongo]
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
>>>>>>> fix-testcontainers-test
```

