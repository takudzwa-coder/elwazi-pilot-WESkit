# WESkit

A GA4GH compliant Workflow-Execution-Service (WES) for Snakemake.

## Running WESkit via Docker Stack

Currently, we recommend running WESkit via Docker stack. 
Other deployment forms e.g. via Kubernetes might be supported at a later stage.
If you want to run WESkit within a different environment, you might want to follow these steps and adapt them to your own requirements.

### Building the Docker container

First, you need to build a WESkit docker image. If you need to set a proxy server you can set assign HTTP_PROXY and HTTPS_PROXY as arguments.

```bash
docker build -t weskit:0.0.1 \
  --build-arg HTTP_PROXY=$HTTP_PROXY \
  --build-arg HTTPS_PROXY=$HTTPS_PROXY \
  ./

docker build -t weskit:0.0.1 ./
```

### Configuration

To run the WESkit Docker stack, you need to set several environmental variables and configure the configuration files.
There are two configuration files for general usage:

  * `config.yaml`: Main configuration file. Usually you only need to change this file.
  * `log_config.yaml`: Configuration of the logging system.

Set the following environmental variables:

  * `REDIS_CONFIG`: Path to redis configuration file.
  * `SHARED_FILESYSTEM_ROOT`: Path to file system directory for application data such as database files, redis files and Snakemake execution data.
  * `WESKIT_CONFIG`: Path to WESkit config.yaml
  * `WESKIT_IMAGE`: Docker image tag (weskit:0.0.1)
  * `WESKIT_ROOT`: Path to WESkit repository
  
### Run Docker stack

Start WESkit using `docker stack` with `docker-stack.yaml`:

```bash
export REDIS_CONFIG=/PATH/TO/REDIS_CONFIG/redis.conf
export SHARED_FILESYSTEM_ROOT=/PATH/TO/DIR/
export WESKIT_CONFIG=/PATH/TO/WESKIT_CONFIG/config.yaml
export WESKIT_IMAGE=weskit:0.0.1
export WESKIT_ROOT=/PATH/TO/WESKIT/

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

## States

### Description

Set by WESkit:
 - **INITIALIZING**: WESkit has initialized a run object. WESkit stores the run in the database and prepares the run by creating a working directory, by processing attachment files and by checking for a valid workflow url. Finally, WESkit sends a task to Celery.
 - **SYSTEM_ERROR**: An error occurred during execution of a run in WESkit; e.g. workflow url is not valid.
 - **CANCELING**: User sends a cancel request to WESkit and this triggers WESkit to send a cancel command to the Celery worker.

Defined by Celery worker:
 - **QUEUED**: WESkit has sent the task to Celery and the Celery worker returns **PENDING** or **RETRY**
 - **RUNNING**: WESkit has sent the task to Celery and the Celery worker returns **STARTED**
 - **COMPLETE**: WESkit has sent the task to Celery and the Celery worker returns **SUCCESS**
 - **EXECUTOR_ERROR**: WESkit has sent the task to Celery and the Celery worker returns **FAILURE**
 - **CANCELED**: WESkit has sent the task to Celery , user canceled the run and the Celery worker returns **REVOKED**

Not set:
 - **UNKNOWN**: This state is not used by WESkit. WESkit knows.
 - **PAUSED**: Pausing a run is not supported by WESkit

### transitions

WESkit controls possible state transitions. Following state changes may occur during lifetime of a single run:

 - **INITIALIZING** to (**QUEUED**, **RUNNING**, **COMPLETE**, **EXECUTOR_ERROR**)
 - (**QUEUED**, **RUNNING**) to (**QUEUED**, **RUNNING**, **COMPLETE**, **EXECUTOR_ERROR**)
 - (**INITIALIZING**, **QUEUED**, **RUNNING**) to **SYSTEM_ERROR**
 - (**QUEUED**, **RUNNING**) to **CANCELING**
 - **CANCELING** to **CANCELED**

