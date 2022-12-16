#  Copyright (c) 2022. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
import math
from abc import ABCMeta, abstractmethod
from pathlib import Path
from typing import List, Dict, Optional, Union

from tempora import parse_timedelta

from weskit.classes.ShellCommand import ShellCommand, ss, ShellSpecial
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
            raise ValueError(f"Non-allowed default parameters for {type(self).name()}: " +
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
    @abstractmethod
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
            return ["source", candidates[0], ss("&&"), "set", "-eu", "-o", "pipefail", ss("&&")]
        else:
            return []

    def _optional_param(self,
                        param: ActualEngineParameter,
                        name: str,
                        argument: str) -> List[str]:
        """
        Helper for parameter processing. This is for flag-like parameters. The boolean value is
        interpreted as presence (True) or absence (False) of the flag.
        """
        def to_bool(value: Optional[str]) -> bool:
            if value is None:
                return False
            elif value.lower() in ["true", "t", "present", "1", "yes", "y"]:
                return True
            elif value.lower() in ["false", "f", "absent", "0", "no", "n"]:
                return False
            else:
                raise ValueError(f"Could not parse '{value}' to boolean")

        if param.param == self.known_parameters()[name]:
            if to_bool(param.value):
                return [argument]
            else:
                return []
        else:
            return []

    def _argument_param(self,
                        param: ActualEngineParameter,
                        name: str,
                        argument: str) -> List[Union[str, ShellSpecial]]:
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
                # environmental varibales e.g. $CONDA_ENVS_PATH need to be evaluated
                # before passed with its respective arument to the command
                if str(param.value).startswith('$'):
                    return [argument, ss(str(param.value))]
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

    @staticmethod
    @abstractmethod
    def name() -> str:
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


class Snakemake(WorkflowEngine):

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
                                              "forceall",
                                              "profile",
                                              "tes",
                                              "jobs",
                                              "conda-prefix",
                                              "data_aws_access_key_id",
                                              "data_aws_secret_access_key",
                                              "task_conda_pkgs_dirs",
                                              "task_conda_envs_path",
                                              "task_home",
                                              "prefix_conda_envs_path"})
                                   .union([list(par.names)[0] for par in super(Snakemake, cls).
                                          known_parameters().all]))

    def _command_params(self, parameters: List[ActualEngineParameter]) -> \
            List[Union[ShellSpecial, str]]:
        result = []
        for param in parameters:
            result += self._argument_param(param, "cores", "--cores")
            result += self._optional_param(param, "use-singularity", "--use-singularity")
            result += self._optional_param(param, "use-conda", "--use-conda")
            result += self._optional_param(param, "forceall", "--forceall")
            result += self._argument_param(param, "profile", "--profile")
            result += self._argument_param(param, "tes", "--tes")
            result += self._argument_param(param, "jobs", "--jobs")
            result += self._argument_param(param, "conda-prefix", "--conda-prefix")
        return result

    # For submission of the workload tasks to e.g. the TES server or a container,
    # we need to pass several environmental variables.
    #
    # * AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY for accessing the S3 storage
    # * CONDA_PKGS_DIRS, CONDA_ENVS_PATH for installation of the new environments
    #                                    on a writable volume mounted into the
    #                                    container
    # * conda-prefix receives the same value as CONDA_ENVS_PATH but is used in
    #                the engine environment (e.g. local/Celery worker side).

    ENVVARS_DICT = {
            "data_aws_access_key_id": "AWS_ACCESS_KEY_ID",
            "data_aws_secret_access_key": "AWS_SECRET_ACCESS_KEY",
            "task_conda_pkgs_dirs": "CONDA_PKGS_DIRS",
            "task_conda_envs_path": "CONDA_ENVS_PATH",
            "task_home": "HOME"
        }

    def _environment(self,
                     workflow_path: Path,
                     parameters: List[ActualEngineParameter]) -> Dict[str, str]:
        result = super()._environment(workflow_path, parameters)

        for var in self.ENVVARS_DICT:
            for p in parameters:
                if p.value is not None:
                    if p.param == self.known_parameters()[var]:
                        result[self.ENVVARS_DICT[var]] = str(p.value)
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
        init: List[Union[ShellSpecial, str]] = ["snakemake", "--snakefile", str(workflow_path)]
        command += init + self._command_params(parameters)

        command += ["--configfile"] + [str(file) for file in config_files]

        filt_params = [self.ENVVARS_DICT[k] for k, v in engine_params.items()
                       if any(k.startswith(x) for x in ["data_", "task_"])]
        if len(filt_params) > 0:
            command += ["--envvars"] + filt_params

        return ShellCommand(command=command,
                            workdir=None if workdir is None else Path(workdir),
                            environment=self._environment(workflow_path, parameters))


class Nextflow(WorkflowEngine):

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
                                              "tempdir"})
                                   .union([list(par.names)[0] for par in super(Nextflow, cls).
                                          known_parameters().all]))

    def _environment(self,
                     workflow_path: Path,
                     parameters: List[ActualEngineParameter]) -> Dict[str, str]:
        result = super()._environment(workflow_path, parameters)
        for param in parameters:
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
