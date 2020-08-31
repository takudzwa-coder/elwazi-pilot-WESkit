from ga4gh.wes.RunStatus import RunStatus
from ga4gh.wes.tasks import run_snakemake
import json
import os
import sys
import yaml


class Snakemake:

    def cancel(self, run, database):
        # ToDo: Cancel a running Snakemake task
        run["run_status"] = RunStatus.CANCELED.encode()
        database.update_run(run)
        return run

    def get_state(self, run):
        running_task = run_snakemake.AsyncResult(run["_celery_task_id"])
        return running_task.state

    def execute(self, run, database, logger):
        print("Snakemake:execute", file=sys.stderr)
        logger.info("RunWorkflow")

        # create run environment
        tmp_dir = "tmp/"
        logger.info("_create_environment")
        run_dir = os.path.abspath(os.path.join(tmp_dir, run["run_id"]))
        if not os.path.exists(run_dir):
            os.makedirs(run_dir)
        with open(run_dir + "/config.yaml", "w") as ff:
            yaml.dump(json.loads(run["request"]["workflow_params"]), ff)
        run["execution_path"] = run_dir
        database.update_run(run)

        # execute run
        logger.info("_execute_run")
        run_kwargs = {
            "snakefile": run["request"]["workflow_url"],
            "workdir": run_dir,
            "configfiles": [os.path.join(run_dir, "config.yaml")]
        }
        run["run_status"] = RunStatus.INITIALIZING.encode()
        run["start_time"] = database.get_current_time()
        run["run_log"]["cmd"] = ", ".join(
            "{}={}".format(key, run_kwargs[key]) for key in run_kwargs.keys()
        )
        database.update_run(run)
        logger.info("_send_run_to_celery")
        task = run_snakemake.apply_async(args=[], kwargs=run_kwargs)
        run["_celery_task_id"] = task.id
        database.update_run(run)
        return run
