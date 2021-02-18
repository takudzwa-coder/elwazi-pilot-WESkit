import os
from weskit.classes.Workflow import Snakemake, Nextflow
from weskit.classes.WorkflowType import WorkflowType
from weskit.tasks.celery import celery_app


@celery_app.task(bind=True)
def run_workflow(self,
                 workflow_type: WorkflowType,
                 workflow_path: os.path,
                 workdir: os.path,
                 config_files: list,
                 **workflow_kwargs):
    outputs = []
    if workflow_type == WorkflowType.SNAKEMAKE.value:
        outputs = Snakemake.run(self, workflow_path, workdir, config_files, **workflow_kwargs)
    elif workflow_type == WorkflowType.NEXTFLOW.value:
        outputs = Nextflow.run(self, workflow_path, workdir, config_files, **workflow_kwargs)
    else:
        raise Exception("Workflow type '" + workflow_type.__str__() + "' is not known")

    return outputs
