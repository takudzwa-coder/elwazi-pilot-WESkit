from ga4gh.wes.RunStatus import RunStatus
import os, subprocess, yaml, json

# get:/runs/{run_id}
class Snakemake:

    # post:/runs/{run_id}/cancel
    def post_run_cancel(self, run_id, database):
        # ToDo: Cancel a running Snakemake process
        print("CancelRun")
        query_result = database.get_run(run_id)
        if query_result is None:
            return {"msg": "Key %s not found" % run_id,
                    "status_code": 0
                    }, 404
        else:
            database.delete_run(run_id)
            return {"run_id": run_id}, 200

    # post:/runs
    def post_run(self, run, database):
        print("RunWorkflow")
        
        # create run environment
        tmp_dir = "tmp/"
        print("_create_environment")
        run_dir = os.path.abspath(os.path.join(tmp_dir, run["run_id"]))
        os.makedirs(run_dir)
        with open(run_dir + "/config.yaml", "w") as ff:
            yaml.dump(json.loads(run["request"]["workflow_params"]), ff)
        run["environment_path"] = run_dir                                                                               # environment_path = workflow_url ?
        database.update_run(run)

        # execute run
        print("_execute_run")
        tmp_dir = "tmp/" + run["run_id"]
        command = [
            "snakemake",
            "--snakefile", run["request"]["workflow_url"],
            "--directory", tmp_dir,
            "all"]
        run["run_status"] = RunStatus.Running.encode()
        run["start_time"] = database.get_current_time()
        run["run_log"]["cmd"] = " ".join(command)
        database.update_run(run)
        with open(tmp_dir + "/stdout.txt", "w") as fout:
            with open(tmp_dir + "/stderr.txt", "w") as ferr:
                subprocess.call(command, stdout=fout, stderr=ferr)
        run["run_status"] = RunStatus.Complete.encode()
        run["end_time"] = database.get_current_time()
        database.update_run(run)
        
        return {k: run[k] for k in ["run_id"]}, 200


