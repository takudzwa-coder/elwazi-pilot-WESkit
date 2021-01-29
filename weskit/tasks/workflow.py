import pathlib
import subprocess
import os
from weskit.tasks.celery import celery_app
from weskit.classes.WorkflowType import WorkflowType
from snakemake import snakemake


@celery_app.task(bind=True)
def run_workflow(self,
                 workflow_type: WorkflowType,
                 workflow_url: os.path,
                 workdir: os.path,
                 configfiles: list,
                 **kwargs):

    outputs = []
    if workflow_type == WorkflowType.SNAKEMAKE.name:
        snakemake(
            snakefile=workflow_url,
            workdir=workdir,
            configfiles=configfiles,
            updated_files=outputs,
            **kwargs)
    elif workflow_type == WorkflowType.NEXTFLOW.name:
        # TODO: Need to redirect output to tmp
        subprocess.run(["nextflow", pathlib.PurePath(workflow_url).name],
                       cwd=str(pathlib.PurePath(workflow_url).parent))
    else:
        raise Exception("Workflow type is not known.")
    return outputs
