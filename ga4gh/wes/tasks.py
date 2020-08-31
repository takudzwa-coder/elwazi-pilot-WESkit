from ga4gh.wes import celery
from snakemake import snakemake


@celery.task(bind=True)
def run_snakemake(self, snakefile, workdir, configfiles, **kwargs):
    snakemake(
        snakefile=snakefile,
        workdir=workdir,
        configfiles=configfiles,
        **kwargs)
    return True
