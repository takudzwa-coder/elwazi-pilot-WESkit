# WESnake

FROM continuumio/miniconda3:4.7.12
SHELL ["/bin/bash", "-c"]

ENV BASH_ENV /root/.bashrc

WORKDIR /

ENV HTTP_PROXY HTTPS_PROXY http_proxy https_proxy NO_PROXY no_proxy
EXPOSE 4080

COPY ./ /wesnake

RUN conda update --prefix /opt/conda conda

RUN conda init bash

RUN /bin/bash -c "\
  cd /wesnake && \
  conda env create -n wesnake -f environment.yaml && \
  source activate wesnake && \
  pip install ./ && \
  conda clean --all -f -y"

# This is to ensure a mounted file will be mounted as file in the container (otherwise it will be a directory).
RUN touch /config.yaml

ENTRYPOINT ["conda", "activate", "wesnake", "&&", \
	    "wesnake", "--config", "/config.yaml"]


