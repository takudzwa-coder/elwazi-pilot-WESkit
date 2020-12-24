from wesnake.tasks.celery import celery_app
from snakemake import snakemake


@celery_app.task(bind=True)
def run_snakemake(self, snakefile, workdir, configfiles, **kwargs):
    outputs = []
    snakemake(
        snakefile=snakefile,
        workdir=workdir,
        configfiles=configfiles,
        updated_files=outputs,
        **kwargs)
    return outputs
