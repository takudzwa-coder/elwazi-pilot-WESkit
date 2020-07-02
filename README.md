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
pip install ./
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

If you followed the installation instructions an executable called `wesnake` is installed. The configurations are provided to the executable by environment variables or command-line options

```bash
export WESNAKE_CONFIG=/path/to/config.yaml
export WESNAKE_LOG_CONFIG=/path/to/log-config.yaml

# For development only.
export WESNAKE_VALIDATION_CONFIG=/path/to/validation.yaml

wesnake
```

or

```bash
wesnake --config config.yaml
```

Note that that if you provide the main configuration via `WESNAKE_CONFIG` you may still override it via the `--config` parameter, but the parameter is not required anymore. In all cases the environment variables are overriden by the command-line arguments.

If you want to run the just the WESnake container you can do similar to this:

```bash
docker run --env WESNAKE_CONFIG=/config --mount type=bind,source=$PWD/tests/config.yaml,target=/config.yaml --user $UID:wesnake --rm wesnake:$version
```

## Running the full stack

Currently, two variants are available for running all redependent tools: Docker Compose and Docker Stack

### Docker Compose

Running the full application with all required services (except the Celery workers) can be done with Docker Compose. You can use the `.env.example` as template for your own `.env`. Put it into the top-level directory of the repository and run

```bash
docker-compose up
```

### Docker Stack

You can use the `docker-compose.yaml` also with `docker stack`. However the way the configuration variables are provided to docker stack is different. You may still want to use the `.env.example` as template. E.g. copy it into `.env`, modify it and run the following command.

```bash
(source <(cat .env | perl -ne 'print "export $_";'); docker stack deploy -c docker-compose.yaml wesnake)
```

This will export all settings from the `.env` file and thus provide them to `docker stack`. Before this works, you may have to do `docker swarm init` or similar, to connect to a swarm.

#### Developer Notes

There are also template `.env.develop` and `docker-compose-devel.yaml` files. Given built container they may run with

```
cd wesnake
mkdir -p compose/volumes/shared
cp tests/config.yaml compose/
wget -o compose/redis.conf https://raw.githubusercontent.com/antirez/redis/6.0/redis.conf
$EDITOR compose/config.yaml
(source <(cat .env.develop | perl -ne 'print "export $_";'); docker stack deploy -c docker-compose-devel.yaml wesnake)
```

Note that the `.env.develop` file configures the stack such that WESnake container mounts the current directory and starts the WESnake REST server from within that directory (`/wesnake-devel`). This means, that any change outside the container will be reflected in the container. To apply the changes you still need to manually restart the `wesnake_rest` container.

The `.env.develop` file sets `WESNAKE_UID` to the current user, while `WESNAKE_GID` is set to "wesnake", which is the group under which Conda and WESnake are installed in the container. Thus it is possible to use the same user ID inside the container and on the host. Files created in the wesnake container are then created with permissions such that the developer may be access them. The support containers (MongoDB, Redis) use their default permissions and their data is stored in docker-managed volumes.

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

Instead of using a stand-alone MongoDB server, you can retrieve one just for testing via docker:

```bash
MONGODB_URI=docker python -m pytest
```
