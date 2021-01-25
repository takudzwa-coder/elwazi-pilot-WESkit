# WESnake

A GA4GH compliant Workflow-Execution-Service (WES) for Snakemake.

## Running WESnake via Docker Stack

Currently, we recommend running WESnake via Docker stack. 
Other deployment forms e.g. via Kubernetes might be supported at a later stage.
If you want to run WESnake within a different environment, you might want to follow these steps and adapt them to your own requirements.

### Building the Docker container

First, you need to build a WESnake docker image. If you need to set a proxy server you can set assign HTTP_PROXY and HTTPS_PROXY as arguments.

```bash
docker build -t weskit:0.0.1 \
  --build-arg HTTP_PROXY=$HTTP_PROXY \
  --build-arg HTTPS_PROXY=$HTTPS_PROXY \
  ./

docker build -t weskit:0.0.1 ./
```

### Configuration

To run the WESnake Docker stack, you need to set several environmental variables and configure the configuration files.
There are two configuration files for general usage:

  * `config.yaml`: Main configuration file. Usually you only need to change this file.
  * `log_config.yaml`: Configuration of the logging system.

Set the following environmental variables:

  * `REDIS_CONFIG`: Path to redis configuration file.
  * `SHARED_FILESYSTEM_ROOT`: Path to file system directory for application data such as database files, redis files and Snakemake execution data.
  * `WESKI_CONFIG`: Path to WESnake config.yaml
  * `WESKI_IMAGE`: Docker iamge tag (weskit:0.0.1)
  * `WESKI_ROOT`: Path to WESnake repository
  
### Run Docker stack

Start WESnake using `docker stack` with `docker-stack.yaml`:

```bash
export REDIS_CONFIG=/PATH/TO/REDIS_CONFIG/redis.conf
export SHARED_FILESYSTEM_ROOT=/PATH/TO/DIR/
export WESKI_CONFIG=/PATH/TO/WESKI_CONFIG/config.yaml
export WESKI_IMAGE=weskit:0.0.1
export WESKI_ROOT=/PATH/TO/WESKI/

docker stack deploy --compose-file=docker_stack.yaml weskit
```

## Development

For development of new features, it is recommended to install the weskit Conda environment locally and develop and run tests.
All requirements are specified in the Conda environment file `environment.yaml`.
To install the environment you need a working Conda installation and issue in the repository root directory

```bash
conda env create -n weskit -f environment.yaml
```

After that you can activate the environment with

```bash
conda activate weskit
```

Perform a test:

```bash
python -m pytest
```
