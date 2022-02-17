#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

from abc import ABCMeta, abstractmethod
from functools import reduce
from pathlib import Path
from os import PathLike
from typing import List, Dict, Optional

from weskit.classes.ShellCommand import ShellCommand


class WorkflowEngineParam(metaclass=ABCMeta):

    def __init__(self, name):
        self._name = name

    @property
    def name(self) -> str:
        return self._name


class CommandLineParam(WorkflowEngineParam):

    def __init__(self,
                 name: str,
                 value: Optional[str]):
        super().__init__(name)
        self._value = value

    @property
    def value(self) -> Optional[str]:
        return self._value


class EnvironmentVariable(WorkflowEngineParam):

    def __init__(self,
                 name: str,
                 value: str):
        super().__init__(name)
        self._value = value

    @property
    def value(self) -> str:
        return self._value


class WorkflowEngineParams(object):

    def __init__(self,
                 environment: List[EnvironmentVariable],
                 command: List[CommandLineParam],
                 run: List[CommandLineParam]):
        self._environment = environment \
            if environment is not None else []
        self._command = command \
            if command is not None else []
        self._run = run \
            if run is not None else []

    @property
    def environment(self) -> List[EnvironmentVariable]:
        return self._environment

    @property
    def command(self) -> List[CommandLineParam]:
        return self._command

    @property
    def run(self) -> List[CommandLineParam]:
        return self._run


class WorkflowEngine(metaclass=ABCMeta):

    @abstractmethod
    def __init__(self,
                 default_params: WorkflowEngineParams):
        self.default_params = default_params

    def _environment(self) -> Dict[str, str]:
        """
        Get a dictionary of environment parameters.
        """
        return dict(map(lambda param: (param.name, param.value),
                        self.default_params.environment))

    @staticmethod
    def _workflow_engine_cli_param(param: CommandLineParam) -> List[str]:
        result = [param.name]
        if param.value is not None:
            result += [str(param.value)]
        return result

    @staticmethod
    def _workflow_engine_cli_params(params: List[CommandLineParam]) -> List[str]:
        return reduce(
            lambda acc, v: acc + v,
            map(lambda wep: WorkflowEngine._workflow_engine_cli_param(wep),
                params),
            [])

    def _command_params(self) -> List[str]:
        """
        Get a list of command-line parameters to be inserted into the command-line.
        """
        return self._workflow_engine_cli_params(self.default_params.command)

    @abstractmethod
    def command(self,
                workflow_path: str,
                workdir: PathLike,
                config_files: List[str],
                workflow_engine_params: List[WorkflowEngineParam]) \
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

    def __init__(self,
                 default_params: WorkflowEngineParams):
        super().__init__(default_params)

    @staticmethod
    def name():
        return "SMK"

    def command(self,
                workflow_path: str,
                workdir: PathLike,
                config_files: List[str],
                workflow_engine_params: List[WorkflowEngineParam])\
            -> ShellCommand:
        command = ["snakemake", "--snakefile", workflow_path] + self._command_params()
        if config_files:
            command += ["--configfile"] + list(map(lambda p: str(p), config_files))
        return ShellCommand(command=command,
                            workdir=Path(workdir),
                            environment=self._environment())


class Nextflow(WorkflowEngine):

    def __init__(self,
                 default_params: WorkflowEngineParams,):
        super().__init__(default_params)

    @staticmethod
    def name():
        return "NFL"

    def _run_command_params(self) -> List[str]:
        """
        An additional parameter slot for `nextflow run`.
        """
        return WorkflowEngine._workflow_engine_cli_params(self.default_params.run)

    def command(self,
                workflow_path: str,
                workdir: PathLike,
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
                            workdir=Path(workdir),
                            environment=self._environment())


class WorkflowEngineFactory:

    @staticmethod
    def _process_env_slot(params: List[dict], tag: str) -> \
            List[EnvironmentVariable]:
        return list(map(lambda param: EnvironmentVariable(name=param["name"],
                                                          value=param["value"]),
                        filter(lambda param: tag in param["slot"],
                               params)))

    @staticmethod
    def _process_cli_slot(params: List[dict], tag: str) -> \
            List[CommandLineParam]:
        return list(map(lambda param: CommandLineParam(name=param["name"],
                                                       value=param.get("value", None)),
                        filter(lambda param: tag in param["slot"],
                               params)))

    @staticmethod
    def _process_params_list(params: List[Dict[str, str]]) -> WorkflowEngineParams:
        environment_params = \
            WorkflowEngineFactory._process_env_slot(params, "environment")
        command_params = \
            WorkflowEngineFactory._process_cli_slot(params, "command")
        run_params = \
            WorkflowEngineFactory._process_cli_slot(params, "run")
        return WorkflowEngineParams(environment=environment_params,
                                    command=command_params,
                                    run=run_params)

    @staticmethod
    def _process_versions(cls, engine_params: Dict[str, List[Dict[str, str]]]) -> \
            Dict[str, Dict[str, CommandLineParam]]:
        """
        :param cls: WorkflowEngine class
        :param engine_params: Version name -> List of dictionaries, one for each parameter.
        :return:
        """
        return dict(map(lambda by_version: (by_version[0],
                                            cls(WorkflowEngineFactory.
                                                _process_params_list(by_version[1]))),
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
            _process_versions(Snakemake,
                              engine_params[Snakemake.name()]),
            Nextflow.name(): WorkflowEngineFactory.
            _process_versions(Nextflow,
                              engine_params[Nextflow.name()])
        }
        # The semantics of workflow_type and workflow_engine_parameters is not completely defined
        # yet. There is also a proposal for a workflow_engine_name parameter.
        # Compare https://gitlab.com/one-touch-pipeline/weskit/api/-/issues/91
        # See also https://github.com/ga4gh/workflow-execution-service-schemas/issues/171

        return workflow_engines
