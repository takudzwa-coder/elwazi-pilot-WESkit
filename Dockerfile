# WESnake

FROM continuumio/miniconda3:4.8.2

SHELL ["/bin/bash", "-c"]
ENV BASH_ENV ~/.bashrc

WORKDIR /

EXPOSE 4080

COPY ./ /wesnake

RUN conda init bash

# RUN conda update --prefix /opt/conda conda

RUN cd /wesnake && \
    conda env create -n wesnake -f environment.yaml && \
    source activate wesnake && \
    pip install ./ && \
    conda clean --all -f -y

# This is to ensure a mounted file will be mounted as file in the container (otherwise it will be a directory).
RUN touch /config.yaml



