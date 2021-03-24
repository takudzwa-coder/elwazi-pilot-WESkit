import os

from weskit.tasks.WorkflowTask import WorkflowTask
from weskit.tasks.celery import celery_app


@celery_app.task(bind=True)
def run_workflow(self,
                 workflow_type: str,
                 workflow_path: os.path,
                 workdir: os.path,
                 config_files: list,
                 **workflow_kwargs):
    return WorkflowTask().run(workflow_type,
                              workflow_path,
                              workdir,
                              config_files,
                              **workflow_kwargs)
