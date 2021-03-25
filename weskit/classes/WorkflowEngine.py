import os
import pathlib
import subprocess
import logging
from abc import ABCMeta, abstractmethod
from typing import List

from weskit.utils import get_current_timestamp
from weskit.utils import get_absolute_file_paths
from weskit.utils import to_uri
from snakemake import snakemake
from dataclasses import dataclass


@dataclass()
class WorkflowEngineParam(object):
    name: str
    type: str
    value: str


class WorkflowEngine(metaclass=ABCMeta):
    @abstractmethod
    def __init__(self, default_params: List[WorkflowEngineParam]):
        self.default_params = default_params

    @staticmethod
    @abstractmethod
    def run(workflow_path: os.path,
            workdir: os.path,
            config_files: list,
            workflow_engine_params: list,
            **workflow_kwargs):
        pass

    @abstractmethod
    def run_workflow_engine_params(self, params: List[WorkflowEngineParam])\
            -> List[str]:
        """
        Take a list of WorkflowEngineParams for a specific run and combine
        them with the self.default_engine_params. The return value is a list
        of command-line parameters that can directly be inserted into the
        workflow manager call.
        :param params:
        :return:
        """
        pass

    @staticmethod
    @abstractmethod
    def name() -> str:
        pass

    @staticmethod
    @abstractmethod
    def version() -> str:
        pass


class Snakemake_5(WorkflowEngine):  # noqa
    def __init__(self, default_params: List[WorkflowEngineParam]):
        super().__init__(default_params)

    @staticmethod
    def run(workflow_path: os.path,
            workdir: os.path,
            config_files: list,
            workflow_engine_params: list,
            **workflow_kwargs):
        logging.getLogger().info("run_snakemake: {}, {}, {}".
                                 format(workflow_path, workdir, config_files))
        outputs = []
        snakemake(
            snakefile=workflow_path,
            workdir=workdir,
            configfiles=config_files,
            updated_files=outputs,
            **workflow_kwargs)
        return outputs

    @staticmethod
    def name():
        return "snakemake"

    @staticmethod
    def version():
        return "5"

    def run_workflow_engine_params(self, params: List[WorkflowEngineParam]) \
            -> List[str]:
        """
        TODO Implement this!
        """
        return []


class Nextflow_20(WorkflowEngine):  # noqa
    def __init__(self, default_params: List[WorkflowEngineParam]):
        super().__init__(default_params)

    @staticmethod
    def run(workflow_path: os.path,
            workdir: os.path,
            config_files: list,
            workflow_engine_params: list,
            **workflow_kwargs):
        logging.getLogger().info("run_nextflow: {}, {}, {}".
                                 format(workflow_path, workdir, config_files))
        timestamp = get_current_timestamp()
        # TODO Require a profile configuration.
        # TODO Handle WFMS-specific settings, such as Java memory settings
        # TODO Make use of kwargs. Ensure same semantics as for Snakemake.
        # TODO Always use -with-trace, -resume, -offline
        # TODO Always use -with-timeline
        command = ["nextflow", "run", workflow_path]
        with open(os.path.join(workdir, "command"), "a") as commandOut:
            print("{}: {}, workddir={}".format(timestamp, command, workdir),
                  file=commandOut)
            # Timestamp-writes are flushed to ensure they are written before
            # the workflows stderr and stdout.
            with open(os.path.join(workdir, "stderr"), "a") as stderr:
                print(timestamp, file=stderr, flush=True)

                with open(os.path.join(workdir, "stdout"), "a") as stdout:
                    print(timestamp, file=stdout, flush=True)
                    result = \
                        subprocess.run(command,
                                       cwd=str(pathlib.PurePath(workdir)),
                                       stdout=stdout,
                                       stderr=stderr)
            print("{}: exit code = {}".
                  format(get_current_timestamp(), result.returncode),
                  file=commandOut, flush=True)
        # TODO What to do if completed_process.returncode != 0?
        outputs = to_uri(get_absolute_file_paths(workdir))
        return outputs

    @staticmethod
    def name():
        return "nextflow"

    @staticmethod
    def version():
        return "20"

    def run_workflow_engine_params(self, params: List[WorkflowEngineParam]) \
            -> List[str]:
        """
        TODO Implement this!
        """
        return []


class WorkflowEngineFactory:

    @staticmethod
    def _extract_workflow_engine_params(config: List[dict],
                                        workflow_type: str)\
            -> List[WorkflowEngineParam]:
        return list(map(WorkflowEngineFactory._extract_workflow_engine_param,
                        filter(lambda val:
                               val["workflow_engine"] == workflow_type,
                               config)))

    @staticmethod
    def _extract_workflow_engine_param(config: dict) -> WorkflowEngineParam:
        """Take a dictionary with name, type and value/default_value fields,
        and create a WorkflowEngineParam() instance from it."""
        assert not ("value" in config and "default_value" in config)
        return WorkflowEngineParam(name=config["name"],
                                   type=config["type"],
                                   value=config.get("value",
                                                    config["default_value"]))

    @staticmethod
    def workflow_engine_index(config: dict) -> dict:
        """Return a dictionary of all WorkflowEngines mapping workflow_engine
         to WorkflowEngine instances.

         This is yet statically implemented, but could at some
         point by done with https://stackoverflow.com/a/3862957/8784544.
         """
        all_engine_params =\
            config.get("static_service_info"). \
            get("default_workflow_engine_parameters")
        workflow_engines = {
            Snakemake_5.name():
                Snakemake_5(WorkflowEngineFactory.
                            _extract_workflow_engine_params
                            (all_engine_params, Snakemake_5.name())),
            Nextflow_20.name():
                Nextflow_20(WorkflowEngineFactory.
                            _extract_workflow_engine_params
                            (all_engine_params, Nextflow_20.name()))
        }
        return workflow_engines
