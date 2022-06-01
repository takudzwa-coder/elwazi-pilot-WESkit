#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

FROM continuumio/miniconda3:4.9.2

EXPOSE 5000

# Capitalized versions for many tools. Minuscle version at least for apt.
ARG HTTP_PROXY=""
ARG http_proxy="$HTTP_PROXY"
ARG HTTPS_PROXY=""
ARG https_proxy="$HTTPS_PROXY"
ARG NO_PROXY=""
ARG no_proxy="$NO_PROXY"

# Use (likely) unused user and group IDs by default.
ARG USER=weskit
ARG GROUP=weskit
ARG USER_ID="35671"
ARG GROUP_ID="35671"

RUN groupadd -r "$GROUP" -g "$GROUP_ID" && \
	useradd -r -s /bin/false -m -d /home/weskit -g "$GROUP" -u "$USER_ID" "$USER"

RUN mkdir /weskit \
    && chown -R "$USER:$GROUP" /weskit /opt/conda \
    && chmod -R 0770 /home/weskit /weskit /opt/conda \
    && umask 0770

USER $USER:$GROUP

# For development bind your weskit repository to /weskit. It needs to be readable by the
# USER_ID that is used here. You can for instance use your personal user and group IDs.
#
# For production, directly build the container with the correct repository version checked out.
# Use a user and group ID available on the deployment system.
WORKDIR /weskit

# Set up the Conda environment

# /home/weskit is used for the shell configuration (for Conda!) and the configuration files.
SHELL ["/bin/bash", "-c"]

# BASH_ENV needs to be set for the Conda setup.
ENV BASH_ENV /home/weskit/.bashrc

RUN conda init bash

RUN conda config --set proxy_servers.http "$HTTP_PROXY" && \
    conda config --set proxy_servers.https "$HTTPS_PROXY" && \
    echo "Installing mamba ..." && \
    conda install mamba=0.15.3 -n base -c conda-forge \

# Note: With the current Conda version 4.9.2, the environment.yaml must be located in a writable
# directory, or Conda will fail with a permission denied error.
COPY environment.yaml /weskit/environment.yaml
RUN echo "Creating environment ..." && \
    mamba env create -n weskit -f /weskit/environment.yaml && \
    source activate weskit && \
    echo "Cleaning packages ..." && \
    conda clean --all -f -y

# The source code is changing more frequently. Copy it only in the outer layer of the container.
COPY ./ /weskit

# Ensure the following path will be a file, when mounted into the container (otherwise it will be a
# directory).
RUN touch /home/weskit/config.yaml
