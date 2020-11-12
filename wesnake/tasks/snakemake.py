from wesnake.tasks.celery import celery_app
from snakemake import snakemake


@celery_app.task(bind=True)
def run_snakemake(self, snakefile, workdir, configfiles, **kwargs):
    snakemake(
        snakefile=snakefile,
        workdir=workdir,
        configfiles=configfiles,
        **kwargs)
    return True
