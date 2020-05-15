# WESnake

FROM continuumio/miniconda3:4.8.2

SHELL ["/bin/bash", "-c"]
ENV BASH_ENV ~/.bashrc

WORKDIR /

ENV HTTP_PROXY HTTPS_PROXY http_proxy https_proxy NO_PROXY no_proxy
EXPOSE 4080

COPY ./ /wesnake

RUN conda init bash

# RUN conda update --prefix /opt/conda conda

RUN cd /wesnake && \
    conda env create -n wesnake -f environment.yaml && \
    source activate wesnake && \
    pip install ./ && \
    conda clean --all -f -y




