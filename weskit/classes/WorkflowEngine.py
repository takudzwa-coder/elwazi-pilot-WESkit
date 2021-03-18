import os
import pathlib
import subprocess
import logging
from abc import ABCMeta, abstractmethod
from weskit.utils import get_current_timestamp
from weskit.utils import get_absolute_file_paths
from weskit.utils import to_uri
from snakemake import snakemake


class WorkflowEngine(metaclass=ABCMeta):
    @abstractmethod
    def __init__(self, workflow_kwargs: dict):
        self.workflow_kwargs = workflow_kwargs

    @staticmethod
    @abstractmethod
    def run(workflow_path: os.path,
            workdir: os.path,
            config_files: list,
            **workflow_kwargs):
        pass

    @staticmethod
    @abstractmethod
    def name():
        pass


class Snakemake(WorkflowEngine):
    def __init__(self, workflow_kwargs: dict):
        super().__init__(workflow_kwargs)

    @staticmethod
    def run(workflow_path: os.path,
            workdir: os.path,
            config_files: list,
            **workflow_kwargs):
        logging.getLogger().info("Snakemake.run: {}, {}, {}".
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
        return __class__.__name__.lower()


class Nextflow(WorkflowEngine):
    def __init__(self, workflow_kwargs: dict):
        super().__init__(workflow_kwargs)

    @staticmethod
    def run(workflow_path: os.path,
            workdir: os.path,
            config_files: list,
            **workflow_kwargs):
        logging.getLogger().info("Nextflow.run: {}, {}, {}".
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
        return __class__.__name__.lower()


class WorkflowEngineFactory:

    @staticmethod
    def extract_workflow_parameters(config_file: dict,
                                    workflow_tag: str) -> dict:

        kwargs = {}
        if workflow_tag == "snakemake":
            for parameter in (config_file["static_service_info"]
                              ["default_workflow_engine_parameters"]):
                workflow_engine = parameter["workflow_engine"].lower()
                if workflow_engine == "snakemake":
                    kwargs[parameter["name"]] = eval(
                        parameter["type"])(parameter["default_value"])
        elif workflow_tag == "nextflow":
            for parameter in (config_file["static_service_info"]
                              ["default_workflow_engine_parameters"]):
                workflow_engine = parameter["workflow_engine"].lower()
                if workflow_engine == "nextflow":
                    kwargs[parameter["name"]] = eval(
                        parameter["type"])(parameter["default_value"])
        return kwargs

    @staticmethod
    def get_engine(config_file: dict, workflow_type: str):
        try:
            if workflow_type == Snakemake.name():
                return \
                    Snakemake(WorkflowEngineFactory.extract_workflow_parameters
                              (config_file, "snakemake"))
            elif workflow_type == Nextflow.name():
                return \
                    Nextflow(WorkflowEngineFactory.extract_workflow_parameters
                             (config_file, "nextflow"))
            raise AssertionError("Workflow type '" +
                                 workflow_type.__str__() +
                                 "' is not known")
        except AssertionError as e:
            print(e)
