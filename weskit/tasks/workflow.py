import os
from weskit.classes.Workflow import Snakemake, Nextflow
from weskit.tasks.celery import celery_app


@celery_app.task(bind=True)
def run_workflow(self,
                 workflow_type: str,
                 workflow_path: os.path,
                 workdir: os.path,
                 config_files: list,
                 **workflow_kwargs):
    outputs = []
    if workflow_type == Snakemake.name():
        outputs = Snakemake.run(workflow_path,
                                workdir,
                                config_files,
                                **workflow_kwargs)
    elif workflow_type == Nextflow.name():
        outputs = Nextflow.run(workflow_path,
                               workdir,
                               config_files,
                               **workflow_kwargs)
    else:
        raise Exception("Workflow type '" +
                        workflow_type +
                        "' is not known")

    return outputs
