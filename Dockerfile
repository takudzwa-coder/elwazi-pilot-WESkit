# WESnake

FROM continuumio/miniconda3:4.8.2

EXPOSE 4080

COPY ./ /wesnake

# Make all wesnake and conda data owned and readable by all, to allow running the service with
# any user ID in the container (e.g. using --user $UID:$GID notation of docker run). Neither
# directory is writable by any other user. Therefore, to update the conda environment a
# developer, running the container with his/her own UID/GUID, should rebuild the container or
# use a local environment installed in a mounted volume/bound directory.
RUN groupadd -r wesnake && useradd -r -s /bin/false -m -g wesnake wesnake
RUN chown -R wesnake:wesnake /wesnake /opt/conda \
    && chmod -R 0770 /home/wesnake /wesnake /opt/conda \
    && umask 0770
USER wesnake

WORKDIR /home/wesnake

SHELL ["/bin/bash", "-c"]
ENV BASH_ENV /home/wesnake/.bashrc

RUN conda init bash

# RUN conda update --prefix /opt/conda conda

RUN cd /wesnake && \
    conda env create -n wesnake -f environment.yaml && \
    source activate wesnake && \
    pip install ./ && \
    conda clean --all -f -y

# This is to ensure a mounted file will be mounted as file in the container (otherwise it will be a directory).
RUN touch /home/wesnake/config.yaml
