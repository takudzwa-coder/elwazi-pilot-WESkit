import logging
from weskit.classes.WorkflowEngine\
    import Snakemake, Nextflow

logger = logging.getLogger(__name__)


class WorkflowTask:

    # It seems not to be possible to use a non-static method, here. Celery
    # complains that parameter "self" is missing! This is because of a Celery
    # internal test that apparently cannot handle bound method such as
    # `WorkflowTask().run`, in which self is already bound. But then adding
    # "self' to the parameters results in a Python error, that "self" is double
    # in the parameter list.
    #
    # Keeping this in a class still has the advantage that this method can be
    # dynamically bound with `celery_app.task(WorkflowTask.run)`.
    @staticmethod
    def run(workflow_type: str,
            workflow_path: str,
            workdir: str,
            config_files: list,
            **workflow_kwargs):
        outputs = []
        if workflow_type == Snakemake.name():
            logger.info("Running Snakemake_5 in %s" % workflow_path)
            outputs = Snakemake.run(workflow_path,
                                    workdir,
                                    config_files,
                                    **workflow_kwargs)
        elif workflow_type == Nextflow.name():
            logger.info("Running Nextflow_20 in %s" % workflow_path)
            outputs = Nextflow.run(workflow_path,
                                   workdir,
                                   config_files,
                                   **workflow_kwargs)
        else:
            raise Exception("Workflow type '" +
                            workflow_type +
                            "' is not known")

        return outputs
