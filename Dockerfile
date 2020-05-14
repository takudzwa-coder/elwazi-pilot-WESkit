# WESnake

FROM continuumio/miniconda3:4.8.2

SHELL ["/bin/bash", "-c"]
ENV BASH_ENV ~/.bashrc

WORKDIR /

ARG HTTP_PROXY_SERVER
ARG HTTPS_PROXY_SERVER
ARG NO_PROXY_LIST


ENV HTTP_PROXY=$HTTP_PROXY_SERVER \
    HTTPS_PROXY=$HTTPS_PROXY_SERVER \
    http_proxy=$HTTP_PROXY_SERVER \
    https_proxy=$HTTPS_PROXY_SERVER \
    NO_PROXY=$NO_PROXY_LIST \
    no_proxy=$NO_PROXY_LIST

COPY environment.yaml /environment.yaml

RUN conda init bash

# RUN conda update --prefix /opt/conda conda

RUN conda config --set proxy_servers.http $HTTP_PROXY_SERVER && \
    conda config --set proxy_servers.https $HTTPS_PROXY_SERVER && \
    conda env update --name base --file environment.yaml && \
    conda clean --all -f -y

# This is to ensure a mounted file will be mounted as file in the container (otherwise it will be a directory).
#RUN touch /config.yaml

ENV PATH /opt/conda/envs/wesnake/bin:$PATH

#COPY ./ /wesnake
#RUN cd /wesnake && \
#    pip install ./
#ENTRYPOINT ["/bin/bash", "-i", "-c"]
#CMD ["wesnake --config /config.yaml"]


