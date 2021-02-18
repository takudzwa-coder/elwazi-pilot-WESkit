import os
import pathlib
import yaml
import subprocess
import logging
from abc import ABCMeta, abstractmethod, ABC
from weskit.classes.WorkflowType import WorkflowType
from weskit.utils import get_current_timestamp
from weskit.utils import get_absolute_file_paths
from weskit.utils import to_uri
from snakemake import snakemake


class Workflow(metaclass=ABCMeta):
    @abstractmethod
    def __init__(self, workflow_kwargs: dict):
        self.workflow_kwargs = workflow_kwargs

    @abstractmethod
    def run(self,
            workflow_path: os.path,
            workdir: os.path,
            config_files: list,
            **workflow_kwargs):
        pass


class Snakemake(Workflow):
    def __init__(self, workflow_kwargs: dict):
        super().__init__(workflow_kwargs)

    def run(self,
            workflow_path: os.path,
            workdir: os.path,
            config_files: list,
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


class Nextflow(Workflow):
    def __init__(self, workflow_kwargs: dict):
        super().__init__(workflow_kwargs)

    def run(self,
            workflow_path: os.path,
            workdir: os.path,
            config_files: list,
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
            print("{}: {}".format(timestamp, command), file=commandOut)
            # Timestamp-writes are flushed to ensure they are written before the
            # workflows stderr and stdout.
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


class WorkflowFactory:

    def __init__(self, config_file: dict) -> None:

        self.workflow_kwargs = {}
        for parameter in (config_file["static_service_info"]
        ["default_workflow_engine_parameters"]):
            workflow_engine = parameter["workflow_engine"].lower()
            if workflow_engine == "snakemake":
                self.workflow_kwargs[parameter["name"]] = eval(
                    parameter["type"])(parameter["default_value"])
            elif workflow_engine == "nextflow":
                self.workflow_kwargs[parameter["name"]] = eval(
                    parameter["type"])(parameter["default_value"])

    @staticmethod
    def get_workflow(self, workflow_type: WorkflowType):
        try:
            if workflow_type == WorkflowType.SNAKEMAKE:
                return Snakemake(self.workflow_kwargs)
            elif workflow_type == WorkflowType.NEXTFLOW:
                return Nextflow(self.workflow_kwargs)
            raise AssertionError("Workflow type '" + workflow_type.__str__() + "' is not known")
        except AssertionError as _e:
            print(_e)
