import os
import pathlib
import subprocess
import logging
from abc import ABCMeta, abstractmethod
from typing import List, Dict

from weskit.utils import get_current_timestamp
from weskit.utils import get_absolute_file_paths
from weskit.utils import to_uri
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
    def _command(workflow_path, config_files=None):
        pass

    @classmethod
    def run(cls, workflow_path: str,
            workdir: str,
            config_files: list,
            workflow_type: str,
            workflow_engine_params: list,
            **workflow_kwargs):

        command = cls._command(workflow_path, config_files)

        logging.getLogger().info("{}.run: {}, {}, {}"
                                 .format(workflow_type, workflow_path, workdir, config_files))
        timestamp = get_current_timestamp()

        with open(os.path.join(workdir, "command"), "a") as commandOut:
            print("{}: {}, workddir={}".format(timestamp, command, workdir),
                  file=commandOut)

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

        outputs = to_uri(get_absolute_file_paths(workdir))
        return outputs

    @abstractmethod
    def _run_workflow_engine_params(self, params: List[WorkflowEngineParam])\
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


class Snakemake(WorkflowEngine):  # noqa
    def __init__(self, default_params: List[WorkflowEngineParam]):
        super().__init__(default_params)

    @staticmethod
    def _command(workflow_path, config_files):
        command = ["snakemake", "--snakefile", workflow_path, "--cores", "1"]
        if config_files:
            command += ["--configfile"] + config_files
        return command

    @staticmethod
    def name():
        return "snakemake"

    def _run_workflow_engine_params(self, params: List[WorkflowEngineParam]) \
            -> List[str]:
        """
        TODO Implement this!
        """
        return []


class Nextflow(WorkflowEngine):  # noqa
    def __init__(self, default_params: List[WorkflowEngineParam]):
        super().__init__(default_params)

    @staticmethod
    def _command(workflow_path, config_files):
        return ["nextflow", "run", workflow_path]

    @staticmethod
    def name():
        return "nextflow"

    def _run_workflow_engine_params(self, params: List[WorkflowEngineParam]) \
            -> List[str]:
        """
        TODO Implement this!
        """
        return []


class WorkflowEngineFactory:

    @staticmethod
    def _extract_workflow_engine_params(config: Dict[dict, dict])\
            -> List[WorkflowEngineParam]:
        return [WorkflowEngineParam(name=k,
                                    type=config[k]["type"],
                                    value=config[k]["default_value"])
                for k in config.keys()]

    @staticmethod
    def workflow_engine_index(engine_params: dict) -> dict:
        """Return a dictionary of all WorkflowEngines mapping workflow_engine
         to WorkflowEngine instances.

         This is yet statically implemented, but could at some
         point by done with https://stackoverflow.com/a/3862957/8784544.
         """
        workflow_engines = {
            Snakemake.name():
                Snakemake(WorkflowEngineFactory.
                          _extract_workflow_engine_params
                          (engine_params[Snakemake.name()])),
            Nextflow.name():
                Nextflow(WorkflowEngineFactory.
                         _extract_workflow_engine_params
                         (engine_params[Nextflow.name()]))
        }
        return workflow_engines
