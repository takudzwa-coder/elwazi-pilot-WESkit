import logging
from weskit.classes.WorkflowEngine\
    import Snakemake, Nextflow

logger = logging.getLogger(__name__)


def run_workflow(workflow_type: str,
                 workflow_path: str,
                 workdir: str,
                 config_files: list,
                 **workflow_kwargs):
    outputs = []
    if workflow_type == Snakemake.name():
        logger.info("Running Snakemake in %s" % workflow_path)
        outputs = Snakemake.run(workflow_path,
                                workdir,
                                config_files,
                                workflow_type,
                                **workflow_kwargs)
    elif workflow_type == Nextflow.name():
        logger.info("Running Nextflow in %s" % workflow_path)
        outputs = Nextflow.run(workflow_path,
                               workdir,
                               config_files,
                               workflow_type,
                               **workflow_kwargs)
    else:
        raise Exception("Workflow type '" +
                        workflow_type +
                        "' is not known")

    return outputs
