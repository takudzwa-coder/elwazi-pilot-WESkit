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

    configfile = open(os.path.join(workdir, "nextflow.config"), "x")
    configfile.write("workDir = '" + workdir + "'")
    configfile.close()

    job_id_str = str(uuid.uuid4().hex)
    job_id = ''.join([i for i in job_id_str if not i.isdigit()])

    subprocess.run(["nextflow", "-c", os.path.join(workdir, "nextflow.config"),
                    "-log", os.path.join(workdir, "nextflow.log"),
                    "run", "-name", job_id,
                    pathlib.PurePath(workflow_url).name],
                   cwd=str(pathlib.PurePath(workflow_url).parent))
    if os.path.exists(os.path.join(pathlib.PurePath(workflow_url).parent,
                                   ".nextflow")):
        shutil.rmtree(os.path.join(pathlib.PurePath(workflow_url).parent,
                                   ".nextflow"))

    return outputs
