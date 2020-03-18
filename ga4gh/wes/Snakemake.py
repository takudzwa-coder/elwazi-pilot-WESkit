from ga4gh.wes.RunStatus import RunStatus
from flask import current_app
import os, subprocess, yaml, json


class Snakemake:

    def cancel(self, run, database):
        # ToDo: Cancel a running Snakemake process
        run["run_status"] = RunStatus.CANCELED.encode()
        database.update_run(run)
        return run

    def execute(self, run, database):
        current_app.logger.info("RunWorkflow")
        
        # create run environment
        tmp_dir = "tmp/"
        current_app.logger.info("_create_environment")
        run_dir = os.path.abspath(os.path.join(tmp_dir, run["run_id"]))
        os.makedirs(run_dir)
        with open(run_dir + "/config.yaml", "w") as ff:
            yaml.dump(json.loads(run["request"]["workflow_params"]), ff)
        run["execution_path"] = run_dir                                                                               # environment_path = workflow_url ?
        database.update_run(run)

        # execute run
        current_app.logger.info("_execute_run")
        tmp_dir = "tmp/" + run["run_id"]
        command = [
            "snakemake",
            "--snakefile", run["request"]["workflow_url"],
            "--directory", tmp_dir,
            "all"]
        run["run_status"] = RunStatus.RUNNING.encode()
        run["start_time"] = database.get_current_time()
        run["run_log"]["cmd"] = " ".join(command)
        database.update_run(run)
        with open(tmp_dir + "/stdout.txt", "w") as fout:
            with open(tmp_dir + "/stderr.txt", "w") as ferr:
                subprocess.call(command, stdout=fout, stderr=ferr)
        run["run_status"] = RunStatus.COMPLETE.encode()
        run["end_time"] = database.get_current_time()
        database.update_run(run)
        
        return run


