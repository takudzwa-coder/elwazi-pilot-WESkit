# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

import math
from abc import ABCMeta, abstractmethod
from pathlib import Path
from typing import List, Dict, Optional, Union

from tempora import parse_timedelta

from weskit.classes.ShellCommand import ShellCommand, ss, ShellSpecial
from weskit.classes.PathContext import PathContext
from weskit.classes.WorkflowEngineParameters import \
    ActualEngineParameter, ParameterIndex, KNOWN_PARAMS, EngineParameter
from weskit.classes.executor.Executor import ExecutionSettings
from weskit.exceptions import ClientError
from weskit.memory_units import Memory, Unit
from weskit.utils import mop


class WorkflowEngine(metaclass=ABCMeta):

    def __init__(self,
                 version: str,
                 default_params: List[ActualEngineParameter]):
        not_allowed = list(filter(lambda param: param.param not in self.known_parameters().all,
                                  default_params))
        if len(not_allowed) > 0:
            raise ValueError(f"Non-allowed default parameters for {self.name()}: " +
                             str(not_allowed))
        self.default_params = default_params
        self._version = version

    @property
    def version(self) -> str:
        return self._version

    def _environment(self,
                     workflow_path: Path,
                     parameters: List[ActualEngineParameter]) -> Dict[str, str]:
        return {
            "WESKIT_WORKFLOW_ENGINE": self.name() + "=" + self.version,
            "WESKIT_WORKFLOW_PATH": str(workflow_path)
        }

    @classmethod
    def known_parameters(cls) -> ParameterIndex:
        """
        Get an index of the workflow engine parameters allowed for this WorkflowEngine subclass.

        By default, all parameters related to ExecutionSettings are "known".
        """
        return KNOWN_PARAMS.subset(frozenset({"engine-environment",
                                              "job-name",
                                              "max-memory",
                                              "max-runtime",
                                              "cores",
                                              "group",
                                              "queue",
                                              "accounting-name"}))

    def _engine_environment_setup(self,
                                  params: List[ActualEngineParameter]) \
            -> List[Union[str, ShellSpecial]]:
        """
        Shell code for setting up a base environment in which to call the workflow engine. This is
        *not* meant for setting up just environment variables. The environment variables should be
        set via ShellCommand.environment, because they may be set via the command execution
        mechanism.
        """
        candidates = [p.value
                      for p in params
                      if p.param == self.known_parameters()["engine-environment"]]
        if len(candidates) > 0 and candidates[0] is not None:
            return ["set", "-eu", "-o", "pipefail", ss("&&"), "source", candidates[0], ss("&&")]
        else:
            return []

    def _optional_param(self,
                        param: ActualEngineParameter,
                        name: str,
                        argument: str,
                        invert: bool = False) -> List[str]:
        """
        Helper for parameter processing. This is for flag-like parameters. The boolean value is
        interpreted as presence (True) or absence (False) of the flag.
        """
        def to_bool(value: Optional[str], invert: bool = False) -> bool:
            if value is None:
                return False
            elif value.lower() in ["true", "t", "present", "1", "yes", "y"]:
                if invert:
                    return False
                else:
                    return True
            elif value.lower() in ["false", "f", "absent", "0", "no", "n"]:
                if invert:
                    return True
                else:
                    return False
            else:
                raise ValueError(f"Could not parse '{value}' to boolean")

        if param.param == self.known_parameters()[name]:
            if to_bool(param.value, invert):
                return [argument]
            else:
                return []
        else:
            return []

    def _argument_param(self,
                        param: ActualEngineParameter,
                        name: str,
                        argument: str) -> List[str]:
        """
        Helper for parameter processing. This processor is for arguments of the type key/value,
        with an obligatory value (i.e. the value must not be None). If the parameter is None
        (not the string 'None'), then the parameter is removed (e.g. to turn off a set default
        parameter).
        """
        if param.param == self.known_parameters()[name]:
            if param.value is None:
                return []
            else:
                return [argument, str(param.value)]
        else:
            return []

    def _normalize_and_check(self, run_params: Dict[str, Optional[str]]) \
            -> Dict[EngineParameter, Optional[str]]:
        """
        Normalized to `Optional[str]` (they could be e.g. `int` if they come from a JSON parser)
        and check that they are among the known parameters for this WorkflowEngine class. Throws
        a KeyError, if the run_parameter name (key) is not among the known parameters.
        """
        result: Dict[EngineParameter, Optional[str]] = {}
        for name, value in run_params.items():
            parameter = self.known_parameters()[name]
            result[parameter] = None if value is None else str(value)
        return result

    def _effective_run_params(self, run_params: Dict[str, Optional[str]]) \
            -> List[ActualEngineParameter]:
        """
        Combine the run (engine) parameters with the default engine parameters. Check the
        validity of the resulting parameter set and return a lists of WorkflowEngineParam objects
        that will be converted to the actual command-line arguments, etc. later.

        If a run-parameter is not among the known parameters or forbidden to be set, then a
        KeyError is thrown.
        """
        checked_run_params = {
            # We map here to avoid excessive if-else statements in the code below.
            p: ActualEngineParameter(p, v) for p, v in self._normalize_and_check(run_params).items()
        }
        result: List[ActualEngineParameter] = []
        for default_param in self.default_params:
            if default_param.is_api_parameter:
                result += [checked_run_params.get(default_param.param, default_param)]
            else:
                if default_param.param in checked_run_params.keys():
                    raise ClientError(f"Parameter {default_param.param.names} is forbidden")
                result += [default_param]
        return result

    @abstractmethod
    def command(self,
                workflow_path: Path,
                workdir: Optional[Path],
                config_files: List[Path],
                engine_params: Dict[str, Optional[str]]) \
            -> ShellCommand:
        """
        Use the instance variables and run parameters to compose a command to be executed
        by the run method. The workflow_engine_params are just a list of parameters. It is a
        responsibility of the WorkflowEngine implementation to sort these into slots and
        check whether they are allowed to be set or not.
        """
        pass

    @abstractmethod
    def name(self) -> str:
        pass

    def execution_settings(self,
                           engine_params: Dict[str, Optional[str]]) -> ExecutionSettings:

        # Concerning type: This works with ParameterIndex.get() because ParameterIndex
        # is generic and here it is ParameterIndex[ActualEngineParameter].
        def get_value(parameter: Optional[ActualEngineParameter]) -> Optional[str]:
            if parameter is None:
                return None
            else:
                return parameter.value

        parameter_idx = ParameterIndex(self._effective_run_params(engine_params))
        return ExecutionSettings(
            job_name=get_value(parameter_idx.get("job-name")),
            accounting_name=get_value(parameter_idx.get("accounting-name")),
            group=get_value(parameter_idx.get("group")),
            walltime=mop(get_value(parameter_idx.get("max-runtime")), parse_timedelta),
            memory=mop(get_value(parameter_idx.get("max-memory")), Memory.from_str),
            queue=get_value(parameter_idx.get("queue")),
            cores=mop(get_value(parameter_idx.get("cores")), int))


class ActualWorkflowEngine(WorkflowEngine, metaclass=ABCMeta):

    def __init__(self,
                 version: str,
                 default_params: List[ActualEngineParameter]):
        super().__init__(version, default_params)


class Snakemake(ActualWorkflowEngine):

    def __init__(self,
                 version: str,
                 default_params: List[ActualEngineParameter]):
        super().__init__(version, default_params)

    @staticmethod
    def name():
        return "SMK"

    @classmethod
    def known_parameters(cls) -> ParameterIndex:
        return KNOWN_PARAMS.subset(frozenset({"cores",
                                              "use-singularity",
                                              "use-conda",
                                              "resume",
                                              "profile",
                                              "tes",
                                              "jobs",
                                              "data-aws-access-key-id",
                                              "data-aws-secret-access-key",
                                              "task-conda-pkgs-dir",
                                              "task-conda-envs-path",
                                              "task-home",
                                              "prefix_conda_envs_path",
                                              "wms-monitor",
                                              "wms-monitor-arg"})
                                   .union([list(par.names)[0] for par in super(Snakemake, cls).
                                          known_parameters().all]))

    def _command_params(self, parameters: List[ActualEngineParameter]) -> \
            List[str]:
        result = []
        for param in parameters:
            result += self._argument_param(param, "cores", "--cores")
            result += self._optional_param(param, "use-singularity", "--use-singularity")
            result += self._optional_param(param, "use-conda", "--use-conda")
            result += self._optional_param(param, "resume", "--forceall", invert=True)
            result += self._argument_param(param, "profile", "--profile")
            result += self._argument_param(param, "tes", "--tes")
            result += self._argument_param(param, "jobs", "--jobs")
            result += self._argument_param(param, "wms-monitor", "--wms-monitor")
            result += self._argument_param(param, "wms-monitor-arg", "--wms-monitor-arg")
        return result

    # For submission of the workload tasks to e.g. the TES server or a container,
    # we need to pass several environmental variables.
    #
    # * AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY for accessing the S3 storage
    # * CONDA_PKGS_DIRS, CONDA_ENVS_PATH for installation of the new environments
    #                                    on a writable volume mounted into the container

    ENVVARS_DICT = {
            "data-aws-access-key-id": "AWS_ACCESS_KEY_ID",
            "data-aws-secret-access-key": "AWS_SECRET_ACCESS_KEY",
            "task-conda-pkgs-dir": "CONDA_PKGS_DIRS",
            "task-conda-envs-path": "CONDA_ENVS_PATH",
            "task-home": "HOME"
        }

    def _environment(self,
                     workflow_path: Path,
                     parameters: List[ActualEngineParameter]) -> Dict[str, str]:
        result = super()._environment(workflow_path, parameters)

        for var in self.ENVVARS_DICT:
            for param in parameters:
                if param.value is not None:
                    if param.param == self.known_parameters()[var]:
                        result[self.ENVVARS_DICT[var]] = str(param.value)
        return result

    def command(self,
                workflow_path: Path,
                workdir: Optional[Path],
                config_files: List[Path],
                engine_params: Dict[str, Optional[str]])\
            -> ShellCommand:
        parameters = self._effective_run_params(engine_params)
        command = super()._engine_environment_setup(parameters)

        # explicit annotation for your list is required
        init: List[str] = ["snakemake", "--snakefile", str(workflow_path)]
        command += init + self._command_params(parameters)

        command += ["--configfile"] + [str(file) for file in config_files]

        filt_params = [self.ENVVARS_DICT[k] for k, v in engine_params.items()
                       if k in self.ENVVARS_DICT.keys()]
        if len(filt_params) > 0:
            command += ["--envvars"] + filt_params

        return ShellCommand(command=command,
                            workdir=None if workdir is None else Path(workdir),
                            environment=self._environment(workflow_path, parameters))


class Nextflow(ActualWorkflowEngine):

    def __init__(self,
                 version: str,
                 default_params: List[ActualEngineParameter]):
        super().__init__(version, default_params)

    @staticmethod
    def name():
        return "NFL"

    @classmethod
    def known_parameters(cls) -> ParameterIndex:
        return KNOWN_PARAMS.subset(frozenset({"trace",
                                              "report",
                                              "timeline",
                                              "graph",
                                              "max-memory",
                                              "tempdir",
                                              "resume",
                                              "nxf-work",
                                              "with-tower",
                                              "tower-access-token",
                                              "nxf-assets",
                                              "workflow-revision"})
                                   .union([list(par.names)[0] for par in super(Nextflow, cls).
                                          known_parameters().all]))

    ENVVARS_DICT = {
        "tower-access-token": "TOWER_ACCESS_TOKEN",
        "nxf-assets": "NFX_ASSETS"
    }

    def _environment(self,
                     workflow_path: Path,
                     parameters: List[ActualEngineParameter]) -> Dict[str, str]:
        result = super()._environment(workflow_path, parameters)

        for var in self.ENVVARS_DICT:
            for param in parameters:
                if param.param == self.known_parameters()[var]:
                    if param.value is not None:
                        result[self.ENVVARS_DICT[var]] = str(param.value)
                if param.param == self.known_parameters()["max-memory"]:
                    if param.value is None:
                        raise ValueError("max-memory must have valid value")
                    else:
                        result["NXF_OPTS"] = "-Xmx%sm" % \
                                            math.ceil(Memory.from_str(param.value).
                                                      to(Unit.MEGA, False).value)
        return result

    def _command_params(self, parameters: List[ActualEngineParameter]) -> List[str]:
        result = []
        for param in parameters:
            if param.param == self.known_parameters()["tempdir"]:
                if param.value is not None:
                    result += ["-Djava.io.tmpdir=%s" % param.value]
        return result

    def _run_command_params(self, parameters: List[ActualEngineParameter]) -> List[str]:
        """
        An additional parameter slot for `nextflow run`.
        """
        result = []
        for param in parameters:
            result += self._optional_param(param, "trace", "-with-trace")
            result += self._optional_param(param, "report", "-with-report")
            result += self._optional_param(param, "timeline", "-with-timeline")
            result += self._optional_param(param, "graph", "-with-dag")
            result += self._optional_param(param, "resume", "-resume")
            result += self._argument_param(param, "nxf-work", "-w")
            result += self._optional_param(param, "with-tower", "-with-tower")
            result += self._argument_param(param, "workflow-revision", "-r")
        return result

    def command(self,
                workflow_path: Path,
                workdir: Optional[Path],
                config_files: List[Path],
                engine_params: Dict[str, Optional[str]])\
            -> ShellCommand:
        parameters = self._effective_run_params(engine_params)
        command = super()._engine_environment_setup(parameters)
        command += ["nextflow"] +\
            self._command_params(parameters) +\
            ["run", str(workflow_path)]
        if len(config_files) == 1:
            command += ["-params-file", str(config_files[0])]
        else:
            raise ValueError("Nextflow accepts only a single parameters file (`-params-file`)")

        command += self._run_command_params(parameters)
        return ShellCommand(command=command,
                            workdir=None if workdir is None else Path(workdir),
                            environment=self._environment(workflow_path, parameters))


class ContainerWrappedEngine(WorkflowEngine, metaclass=ABCMeta):

    def __init__(self, actual_engine: ActualWorkflowEngine,
                 executor_context: PathContext):
        self._actual_engine = actual_engine
        self._executor_context = executor_context

    @abstractmethod
    def _container_command(self) -> ShellCommand:
        """" Will return the command prefix 'singularity run ... ' """

    @abstractmethod
    def command(self,
                workflow_path: Path,
                workdir: Optional[Path],
                config_files:  List[Path],
                engine_params: Dict[str, Optional[str]])\
            -> ShellCommand:
        """" Composes a command based on the results of _container_command() and
            self._actual_engine.command()
        """

    @abstractmethod
    def name(self) -> str:
        """" Calls ActualWorkflowEngine.name"""


class SingularityWrappedEngine(ContainerWrappedEngine):

    def __init__(self, actual_engine: ActualWorkflowEngine,
                 executor_context: PathContext):
        super().__init__(actual_engine, executor_context)

    def name(self) -> str:
        return self._actual_engine.name()

    def __repr__(self):
        return 'Singularity + ' + self.name()

    def _container_command(self) -> ShellCommand:

        container_command: List[Union[str, ShellSpecial]]
        container_command = ["singularity", "run",
                             "--no-home", "-e", "--env", "LC_ALL=POSIX",
                             "--bind", ":".join([str(self._executor_context.data_dir),
                                                 str(self._executor_context.data_dir)]),
                             "--bind", ":".join([str(self._executor_context.workflows_dir),
                                                 str(self._executor_context.workflows_dir)]),
                             str(self._executor_context.singularity_engines_dir /
                                 Path(f"{self.name()}_"
                                      f"{self._actual_engine.version}.sif"))
                             ]
        return ShellCommand(command=container_command)

    def command(self,
                workflow_path: Path,
                workdir: Optional[Path],
                config_files:  List[Path],
                engine_params: Dict[str, Optional[str]])\
            -> ShellCommand:

        container_command = self._container_command()

        actual_engine_command = self._actual_engine.command(workflow_path,
                                                            workdir,
                                                            config_files,
                                                            engine_params)
        workflow_commmand: List[Union[str, ShellSpecial]] = \
            container_command.command + actual_engine_command.command

        return ShellCommand(command=workflow_commmand,
                            workdir=actual_engine_command.workdir,
                            environment=actual_engine_command.environment)
