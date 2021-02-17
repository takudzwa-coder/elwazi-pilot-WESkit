import pathlib, subprocess, os, logging
from weskit.tasks.celery import celery_app
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
    # TODO Make use of kwargs
    # TODO Always use -with-trace.
    # TODO Always use -resume.
    # TODO Log the exact command for reproducibility into the output dir.
    # TODO Always use -with-timeline
    # TODO Always use -log
    command = ["nextflow", "run", workflow_path]
    with open(os.path.join(workdir, "command"), "a") as commandOut:
        print("{}: {}".format(timestamp, command), file=commandOut, flush=True)

    with open(os.path.join(workdir, "stderr"), "a") as stderr:
        print(timestamp, file=stderr, flush=True)
        
        with open(os.path.join(workdir, "stdout"), "a") as stdout:
            print(timestamp, file=stdout, flush=True)
            subprocess.run(command,
                           cwd=str(pathlib.PurePath(workdir)),
                           stdout=stdout,
                           stderr=stderr)
    # TODO What to do if completed_process.returncode != 0?
    # TODO Collect the output files from the output directory (all of them).
    outputs = []
    return outputs
