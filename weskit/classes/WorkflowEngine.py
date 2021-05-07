#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import List, Dict


@dataclass()
class WorkflowEngineParam(object):
    name: str
    type: str
    value: str


class WorkflowEngine(metaclass=ABCMeta):

    @abstractmethod
    def __init__(self,
                 default_params: List[WorkflowEngineParam]):
        self.default_params = default_params

    @abstractmethod
    def command(self,
                workflow_path: str,
                workdir: str,
                config_files: List[str],
                workflow_engine_params: List[WorkflowEngineParam],
                **workflow_kwargs)\
            -> List[str]:
        """
        Use the instance variables and run parameters to compose a command to be executed
        by the run method.
        """
        pass

    def _run_workflow_engine_params(self,
                                    params: List[WorkflowEngineParam])\
            -> List[str]:
        """
        Take a list of WorkflowEngineParams for a specific run and combine
        them with the self.default_engine_params. The return value is a list
        of command-line parameters that can directly be inserted into the
        workflow manager call.
        :param params:
        :return:
        """
        return []

    @staticmethod
    @abstractmethod
    def name() -> str:
        pass


class Snakemake(WorkflowEngine):
    def __init__(self, default_params: List[WorkflowEngineParam]):
        super().__init__(default_params)

    @staticmethod
    def name():
        return "snakemake"

    def command(self,
                workflow_path: str,
                workdir: str,
                config_files: list,
                workflow_engine_params: list,
                **workflow_kwargs)\
            -> List[str]:
        command = ["snakemake", "--snakefile", workflow_path, "--cores", "1"]
        if config_files:
            command += ["--configfile"] + config_files
        return command


class Nextflow(WorkflowEngine):
    def __init__(self, default_params: List[WorkflowEngineParam]):
        super().__init__(default_params)

    @staticmethod
    def name():
        return "nextflow"

    def command(self,
                workflow_path: str,
                workdir: str,
                config_files: list,
                workflow_engine_params: list,
                **workflow_kwargs)\
            -> List[str]:
        return ["nextflow", "run", workflow_path]


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
