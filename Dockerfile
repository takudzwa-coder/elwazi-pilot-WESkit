# WESkit

FROM continuumio/miniconda3:4.8.2

EXPOSE 5000

ARG HTTP_PROXY=""
ARG HTTPS_PROXY=""

COPY ./ /weskit

# Make all weskit and conda data owned and readable by all, to allow running the service with
# any user ID in the container (e.g. using --user $UID:$GID notation of docker run). Neither
# directory is writable by any other user. Therefore, to update the conda environment a
# developer, running the container with his/her own UID/GUID, should rebuild the container or
# use a local environment installed in a mounted volume/bound directory.
RUN groupadd -r weskit && useradd -r -s /bin/false -m -g weskit weskit
RUN chown -R weskit:weskit /weskit /opt/conda \
    && chmod -R 0770 /home/weskit /weskit /opt/conda \
    && umask 0770
USER weskit

WORKDIR /home/weskit

SHELL ["/bin/bash", "-c"]
ENV BASH_ENV /home/weskit/.bashrc

RUN conda init bash

# RUN conda update --prefix /opt/conda conda

RUN cd /weskit && \
    conda config --set proxy_servers.http "$HTTP_PROXY" && \
    conda config --set proxy_servers.https "$HTTPS_PROXY" && \
    conda install mamba -n base -c conda-forge && \
    mamba env create -n weskit -f environment.yaml && \
    source activate weskit && \
    pip install ./ && \
    conda clean --all -f -y

# This is to ensure a mounted file will be mounted as file in the container (otherwise it will be a directory).
RUN touch /home/weskit/config.yaml
