import pathlib
import subprocess
import os
import uuid
import shutil
from weskit.tasks.celery import celery_app
from snakemake import snakemake


@celery_app.task(bind=True)
def run_snakemake(self,
                  workflow_url: os.path,
                  workdir: os.path,
                  publish_dir: os.path,
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
                 publish_dir: os.path,
                 configfiles: list,
                 **kwargs):

    outputs = []

    if not str(publish_dir):
        publish_dir = os.path.join(workdir, "output")

    subprocess.run(["nextflow", "run", workflow_url,
                    "--outputDir=" + publish_dir],
                   cwd=str(pathlib.PurePath(workdir)))

    return outputs
