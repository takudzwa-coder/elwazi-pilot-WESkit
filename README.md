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
  * `WESKIT_IMAGE`: Docker iamge tag (weskit:0.0.1)
  * `WESKIT_ROOT`: Path to WESkit repository

#### SSL configuration
##### Deactivate SSL encryption
Usually WESkit uses SSL secured connections, since authentification data were transfered. Nevertheless it is possible to deactivate SSL by editing `uWSGI_Server/uwsgi.ini`. The comment the `https` option out and uncomment the `http` option. Furthermore, the weskit config must be changed to:
```yaml
jwt_config:
    # Only allow JWT cookies to be sent over https. In production, this
    # should likely be True
    JWT_COOKIE_SECURE: false
```
##### Self-Signed Certificates (Development)
It is easily possible to generate a working self-signed certificate by running:
```bash
./uWSGI_Server/generateDevelopmentCerts.sh
```
This script will generate a new certificate if there is not already a certificated in /uWSGI_Server/certs/weskit.*

##### Signed Certificates (Production)
Adapt the secret section at bottom of the `docker_stack.yaml` to the location of your `*.key` and `*.crt` files.

```yaml
secrets:
  weskit.key:
    file: /MyCertificates/weskit.key        ## Change me
  weskit.crt:
    file: /MyCertificates/certs/weskit.crt  ## and me too
```
  
### Run Docker stack

Start WESkit using `docker stack` with `docker-stack.yaml`:

```bash
export REDIS_CONFIG=/PATH/TO/REDIS_CONFIG/redis.conf
export SHARED_FILESYSTEM_ROOT=/PATH/TO/DIR/
export WESKIT_CONFIG=/PATH/TO/WESKIT_CONFIG/config.yaml
export WESKIT_IMAGE=weskit:0.0.1
export WESKIT_ROOT=/PATH/TO/WESKIT/

# create self signed certificates
./uWSGI_Server/generateDevelopmentCerts.sh

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

Start Server outside of a container:
```bash
uwsgi --ini uWSGI_Server/uwsgi.ini
```
**Note:** This is only for debugging the uwsgi config and login-system. Other parts that were related to the workflow submittion / status will throw exeptions, since that requires the further components of the stack.


# FAQ

## The server is not reachable
Use https://localhost:5000 instead of http://localhost:5000.  Unencrypted conections are refused.
