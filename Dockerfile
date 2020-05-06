# WESnake
#
# Usage:
# - Create a configuration. You can use the tests/config.yaml and log_config.yaml as templates.
# - Run the container with
#
#    docker run \
#         -v /path/to/your/config.yaml:config.yaml \
#         -v /path/to/your/log_config.yaml:log_config.yaml \
#         -p 4080:4080 \
#         wesnake
#
# By default port 4080 is used for the WESnake REST service.
FROM continuumio/miniconda3:4.3.27

ENV HTTP_PROXY HTTPS_PROXY http_proxy https_proxy NO_PROXY no_proxy
EXPOSE 4080

RUN conda env create -n wesnake -f environment.yaml
RUN conda activate wesnake
RUN python setup.py install

WORKDIR ./
ENTRYPOINT ["conda", "run", "-n", "wesnake", "wesnake"]
CMD ["--config", "config.yaml", "--log-config", "log_config.yaml"]
