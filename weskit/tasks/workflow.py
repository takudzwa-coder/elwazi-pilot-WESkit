import pathlib
import subprocess
import os
from weskit.tasks.celery import celery_app
from snakemake import snakemake


@celery_app.task(bind=True)
def run_snakemake(self,
                  workflow_url: os.path,
                  workdir: os.path,
                  configfiles: list,
                  **kwargs):

    outputs = []
    snakemake(
        snakefile=workflow_url,
        workdir=workdir,
        configfiles=configfiles,
        updated_files=outputs,
        **kwargs)

    return outputs


@celery_app.task(bind=True)
def run_nextflow(self,
                 workflow_url: os.path,
                 workdir: os.path,
                 configfiles: list,
                 **kwargs):

    outputs = []
    # TODO: Need to redirect output to tmp
    subprocess.run(["nextflow", pathlib.PurePath(workflow_url).name],
                   cwd=str(pathlib.PurePath(workflow_url).parent))
    return outputs
