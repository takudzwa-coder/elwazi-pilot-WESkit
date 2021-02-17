import pathlib
import subprocess
import os
import logging
from weskit.tasks.celery import celery_app
from weskit.utils import get_absolute_file_paths
from weskit.utils import to_uri
from snakemake import snakemake

from weskit.utils import get_current_timestamp


@celery_app.task(bind=True)
def run_snakemake(self,
                  workflow_path: os.path,
                  workdir: os.path,
                  configfiles: list,
                  **kwargs):
    logging.getLogger().info("run_snakemake: {}, {}, {}".
                             format(workflow_path, workdir, configfiles))
    outputs = []
    snakemake(
        snakefile=workflow_path,
        workdir=workdir,
        configfiles=configfiles,
        updated_files=outputs,
        **kwargs)

    return outputs


# TODO Assumptions?
#
# * The configuration files hae been copied into the workdir?
# * The workflow file (URL) copied to workdir?
#
# Check https://www.nextflow.io/docs/latest/cli.html#options
@celery_app.task(bind=True)
def run_nextflow(self,
                 workflow_path: os.path,
                 workdir: os.path,
                 configfiles: list,
                 **kwargs):
    logging.getLogger().info("run_nextflow: {}, {}, {}".
                             format(workflow_path, workdir, configfiles))
    timestamp = get_current_timestamp()
    # TODO Require a profile configuration.
    # TODO Handle WFMS-specific settings, such as Java memory settings
    # TODO Make use of kwargs. Ensure same semantics as for Snakemake.
    # TODO Always use -with-trace, -resume, -offline
    # TODO Log the exact command for reproducibility into the output dir.
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
