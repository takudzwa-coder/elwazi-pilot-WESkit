# WESkit

FROM continuumio/miniconda3:4.9.2

EXPOSE 5000

# Capitalized versions for many tools. Minuscle version at least for apt.
ARG HTTP_PROXY=""
ARG http_proxy=""
ARG HTTPS_PROXY=""
ARG http_proxy=""

# Use (likely) unused user and group IDs by default.
ARG USER=weskit
ARG GROUP=weskit
ARG USER_ID="35671"
ARG GROUP_ID="35671"

COPY ./ /weskit

# For development bind your weskit repository to /weskit. It needs to be readable by the
# USER_ID that is used here. You can for instance use your personal user and group IDs.
#
# For production, directly build the container with the correct repository version checked out.
# Use a user and group ID available on the deployment system.
#
RUN groupadd -r "$GROUP" -g "$GROUP_ID" && \
	useradd -r -s /bin/false -m -d /home/weskit -g "$GROUP" -u "$USER_ID" "$USER"

# LSF software needs access to /tmp.
RUN chown -R "$USER:$GROUP" /weskit /opt/conda \
    && chmod -R 0770 /home/weskit /weskit /opt/conda \
    && umask 0770

USER $USER:$GROUP

# /home/weskit is used for the shell configuration (for Conda!) and the configuration files.
SHELL ["/bin/bash", "-c"]

ENV BASH_ENV /home/weskit/.bashrc

# /weskit is used for the installation of the repository
WORKDIR /weskit

RUN conda init bash

RUN conda config --set proxy_servers.http "$HTTP_PROXY" && \
    conda config --set proxy_servers.https "$HTTPS_PROXY" && \
    conda install mamba -n base -c conda-forge && \
    mamba env create -n weskit -f environment.yaml && \
    source activate weskit && \
    conda clean --all -f -y

# This is to ensure a mounted file will be mounted as file in the container (otherwise it will be a directory).
RUN touch /home/weskit/config.yaml
