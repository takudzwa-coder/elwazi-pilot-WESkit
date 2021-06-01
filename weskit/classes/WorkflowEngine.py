#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from functools import reduce
from typing import List, Dict, Optional

from weskit.classes.ShellCommand import ShellCommand


@dataclass()
class WorkflowEngineParam(object):
    name: str
    value: Optional[str]   # Optional values are for CLI parameters that don't take values.


class WorkflowEngine(metaclass=ABCMeta):

    @abstractmethod
    def __init__(self,
                 default_params: Dict[str, dict],
                 command_param_prefix: str):
        self.default_params = default_params
        self._command_param_prefix = command_param_prefix

    def _environment(self) -> Dict[str, str]:
        """
        Get a dictionary of environment parameters.
        """
        return self.default_params.get("env", {})

    @staticmethod
    def _workflow_engine_cli_param(prefix: str, param: WorkflowEngineParam) -> List[str]:
        result = [prefix + param.name]
        if param.value is not None:
            result += [str(param.value)]
        return result

    @staticmethod
    def _workflow_engine_cli_params(prefix: str, params: List[WorkflowEngineParam]) -> List[str]:
        return reduce(
            lambda acc, v: acc + v,
            map(lambda wep: WorkflowEngine._workflow_engine_cli_param(prefix, wep),
                params),
            [])

    def _command_params(self) -> List[str]:
        """
        Get a list of command-line parameters to be inserted after `nextflow` and before `run`
        into the nextflow command.
        """
        return self._workflow_engine_cli_params(self._command_param_prefix,
                                                self.default_params.get("command", []))

    @abstractmethod
    def command(self,
                workflow_path: str,
                workdir: str,
                config_files: List[str],
                workflow_engine_params: List[WorkflowEngineParam])\
            -> ShellCommand:
        """
        Use the instance variables and run parameters to compose a command to be executed
        by the run method.
        """
        pass

    @staticmethod
    @abstractmethod
    def name() -> str:
        pass


class Snakemake(WorkflowEngine):

    def __init__(self, default_params: Dict[str, dict]):
        super().__init__(default_params, "--")

    @staticmethod
    def name():
        return "snakemake"

    def command(self,
                workflow_path: str,
                workdir: str,
                config_files: List[str],
                workflow_engine_params: List[WorkflowEngineParam])\
            -> ShellCommand:
        command = ["snakemake", "--snakefile", workflow_path] + self._command_params()
        if config_files:
            command += ["--configfile"] + config_files
        return ShellCommand(command=command,
                            workdir=workdir,
                            environment=self._environment())


class Nextflow(WorkflowEngine):

    def __init__(self, default_params: Dict[str, dict]):
        super().__init__(default_params, "-")

    @staticmethod
    def name():
        return "nextflow"

    def _run_command_params(self) -> List[str]:
        """
        An additional parameter slot for `nextflow run`.
        """
        return WorkflowEngine._workflow_engine_cli_params(self._command_param_prefix,
                                                          self.default_params.get("run", []))

    def command(self,
                workflow_path: str,
                workdir: str,
                config_files: List[str],
                workflow_engine_params: List[WorkflowEngineParam])\
            -> ShellCommand:
        command = ["nextflow"] +\
                  self._command_params() +\
                  ["run", workflow_path]
        if len(config_files) == 1:
            command += ["-params-file", config_files[0]]
        else:
            raise ValueError("Nextflow accepts only a single parameters file (`-params-file`)")
        command += self._run_command_params()
        return ShellCommand(command=command,
                            workdir=workdir,
                            environment=self._environment())


class WorkflowEngineFactory:

    @staticmethod
    def _process_list_param_group(kv):
        group = kv[0]
        values = kv[1]
        if group == "env":
            result_values = values
        else:
            result_values = list(map(lambda v: WorkflowEngineParam(name=v["name"],
                                                                   value=v.get("value", None)),
                                     values))
        return kv[0], result_values

    @staticmethod
    def _process_param_groups(groups: dict):
        return dict(map(WorkflowEngineFactory._process_list_param_group, groups.items()))

    @staticmethod
    def _process_versions(cls, engine_params: Dict[str, dict]) -> Dict[str, dict]:
        return dict(map(lambda kv: (kv[0],
                                    cls(WorkflowEngineFactory._process_param_groups(kv[1]))),
                        engine_params.items()))

    @staticmethod
    def workflow_engine_index(engine_params: Dict[str, dict]) -> Dict[str, dict]:
        """
        Return a dictionary of all WorkflowEngines mapping workflow_engine to
        workflow_engine_version to WorkflowEngine instances.

        This is yet statically implemented, but could at some
        point by done with https://stackoverflow.com/a/3862957/8784544.
        """
        workflow_engines = {
            Snakemake.name(): WorkflowEngineFactory.
            _process_versions(Snakemake, engine_params[Snakemake.name()]),
            Nextflow.name(): WorkflowEngineFactory.
            _process_versions(Nextflow, engine_params[Nextflow.name()])
        }
        # The semantics of workflow_type and workflow_engine_parameters is not completely defined
        # yet. There is also a proposal for a workflow_engine_name parameter.
        # Compare https://gitlab.com/one-touch-pipeline/weskit/api/-/issues/91
        # See also https://github.com/ga4gh/workflow-execution-service-schemas/issues/171

        return workflow_engines
