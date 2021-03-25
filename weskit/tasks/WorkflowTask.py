import logging
from weskit.classes.WorkflowEngine\
    import Snakemake_5, Nextflow_20

logger = logging.getLogger(__name__)


class WorkflowTask:

    def run(self,
            workflow_type: str,
            workflow_path: str,
            workdir: str,
            config_files: list,
            **workflow_kwargs):
        outputs = []
        if workflow_type == Snakemake_5.name():
            logger.info("Running Snakemake_5 in %s" % workflow_path)
            outputs = Snakemake_5.run(workflow_path,
                                      workdir,
                                      config_files,
                                      **workflow_kwargs)
        elif workflow_type == Nextflow_20.name():
            logger.info("Running Nextflow_20 in %s" % workflow_path)
            outputs = Nextflow_20.run(workflow_path,
                                      workdir,
                                      config_files,
                                      **workflow_kwargs)
        else:
            raise Exception("Workflow type '" +
                            workflow_type +
                            "' is not known")

        return outputs
