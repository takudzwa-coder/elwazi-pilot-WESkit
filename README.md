# WESnake

A GA4GH compliant Workflow-Execution-Service (WES) for Snakemake.

## Tests

To run the tests with a local MongoDB installation, create and activate the Conda environment as described before. Then start MongoDB 

```bash
mongodb --dbpath=/your/path/to/db
``` 

This will create an new empty database for you, if the path does not exit yet. MongoDB will also only listen on localhost on the default port 27017, which means access from outside to your database should not be possible. You are not protected from users logged in to the same machine though.

In the repository root directory you can then run
```bash
WESNAKE_TEST=mongodb://localhost:27017/ python -m pytest
``` 

to run all tests. When using an IDE you can need to set the MongoDB URI like in the example above.  

### Testcontainers-based testing

TBD

## Installation from sources

```bash
cd wesnake
python setup.py install
```

## Configuration

There are three configuration files for general usage:

  * `config.yaml`: Main configuration file. Usually you only need to change this file.
  * `log_config.yaml`: Configuration of the logging system. 

As a template you can use the configuration in the `tests/` directory.

NOTE: You should not change the `validation.yaml` file, which is only used to validate the configuration yaml.

## Running

An executable called `wesnake` is installed. Run it with

```bash
wesnake --config config.yaml
```

