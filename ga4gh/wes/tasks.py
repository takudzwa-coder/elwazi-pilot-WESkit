#from ga4gh.wes import celery
from celery import shared_task
import random
import time
from snakemake import snakemake
import subprocess

@shared_task
def mul(x, y):
    return x * y

@shared_task(bind=True)
def long_task(self, msg="Test"):
    """Background task that runs a long function with progress reports."""
    verb = ['Starting up', 'Booting', 'Repairing', 'Loading', 'Checking']
    adjective = ['master', 'radiant', 'silent', 'harmonic', 'fast']
    noun = ['solar array', 'particle reshaper', 'cosmic ray', 'orbiter', 'bit']
    message = ''
    total = random.randint(10, 50)
    for i in range(total):
        if not message or random.random() < 0.25:
            message = '{0}: {1} {2} {3}...'.format(
                msg,
                random.choice(verb),
                random.choice(adjective),
                random.choice(noun)
            )
        self.update_state(
            state='PROGRESS',
            meta={'current': i, 'total': total, 'status': message}
        )
        time.sleep(1)
    return {
        'current': 100,
        'total': 100,
        'status': 'Task completed!',
        'result': 42
    }


@shared_task(bind=True)
def run_snakemake(self, snakefile, workdir):

    # TODO: use Snakemake API instead of subprocess call
    #job = snakemake(
    #    snakefile=snakefile,
    #    workdir=workdir
    #)
    
    command = [
        "snakemake",
        "--snakefile", snakefile,
        "--directory", workdir,
        "all"]
    
    with open(workdir + "/stdout.txt", "w") as fout:
        with open(workdir + "/stderr.txt", "w") as ferr:
            subprocess.call(command, stdout=fout, stderr=ferr)
    
    return True