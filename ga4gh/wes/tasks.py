from celery import shared_task
from snakemake import snakemake
import sys

@shared_task(bind=True)
def run_snakemake(self, snakefile, workdir, configfiles, **kwargs):
    snakemake(
        snakefile=snakefile,
        workdir=workdir,
        configfiles=configfiles,
        **kwargs)
    return True
