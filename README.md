# WESnake

A GA4GH compliant Workflow-Execution-Service (WES) for Snakemake.

## Conda environment

All requirements are specified in the Conda environment file `environment.yaml`. To install the environment you need a working Conda installation and issue in the repository root directory

```bash
conda env create -n wesnake -f environment.yaml
``` 

After that you can activate the environment with

```bash
conda activate wesnake
```

## Installation from sources

```bash
cd wesnake
python setup.py install
```

## Building the Docker container

```bash
docker build --rm --build-arg http_proxy=$HTTP_PROXY --build-arg https_proxy=$HTTPS_PROXY -t wesnake:$version ./
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

If you want to run the container, you need to provide a `config.yaml`, e.g. just to try use the `tests/config.yaml` from the repository:

```bash
 docker run --mount type=bind,source=$PWD/tests/config.yaml,target=/config.yaml --rm wesnake:$version
```

TBD: Reduce the size of the container.

## Tests

To run the tests with a local MongoDB installation, create and activate the Conda environment as described before. Then start MongoDB 

```bash
mongodb --dbpath=/your/path/to/db
``` 

This will create an new empty database for you, if the path does not exit yet. MongoDB will only listen on localhost on the default port 27017, which means that access from outside to your database is impossible. You are not protected from users logged in to the same machine, though.

To run the tests from the command line you can now do

```bash
MONGODB_URI=mongodb://localhost:27017/ python -m pytest
``` 

When using an IDE you need to set the MongoDB URI like in the example above.  

### Docker-based Testing

Instead of using a stand-alone MongoDB server, you can retrieve one just for testing via docker:

```bash
MONGODB_URI=docker python -m pytest
```
