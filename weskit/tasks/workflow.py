import pathlib
import subprocess
from weskit.tasks.celery import celery_app
from snakemake import snakemake

@celery_app.task(bind=True)
def run_workflow(self, workflowfile, workdir, configfiles, **kwargs):
    outputs = []

    if pathlib.Path(workflowfile).suffix == ".nf":
        subprocess.run(["nextflow", pathlib.PurePath(workflowfile).name], cwd=str(pathlib.PurePath(workflowfile).parent))
    else:
        snakemake(
            snakefile=workflowfile,
            workdir=workdir,
            configfiles=configfiles,
            updated_files=outputs,
            **kwargs)
    return outputs
