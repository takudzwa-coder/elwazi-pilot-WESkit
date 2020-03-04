from ga4gh.wes.RunStatus import RunStatus
import ga4gh.wes.logging_configs as log
import os, subprocess, yaml, json


def execute_run(current_app, run):
    log_msg = log.log_info("_execute_run")
    new_run = run.copy()
    tmp_dir = "tmp/" + new_run["run_id"]
    command = [
        "snakemake",
        "--snakefile", new_run["request"]["workflow_url"],
        "--directory", tmp_dir,
        "all"]
    new_run["run_status"] = RunStatus.Running.encode()
    new_run["start_time"] = current_app.database.get_current_time()
    new_run["run_log"] = log_msg
    new_run["run_log"]["cmd"] = " ".join(command)
    current_app.database.update_run(new_run)
    with open(tmp_dir + "/stdout.txt", "w") as fout:
        with open(tmp_dir + "/stderr.txt", "w") as ferr:
            subprocess.call(command, stdout=fout, stderr=ferr)
    new_run["run_status"] = RunStatus.Complete.encode()
    new_run["end_time"] = current_app.database.get_current_time()
    current_app.database.update_run(new_run)
    return new_run


def create_environment(current_app, run):
    tmp_dir = "tmp/"
    log_msg = log.log_info("_create_environment")
    run_dir = os.path.abspath(os.path.join(tmp_dir, run["run_id"]))
    os.makedirs(run_dir)
    with open(run_dir + "/config.yaml", "w") as ff:
        yaml.dump(json.loads(run["request"]["workflow_params"]), ff)
    new_run = run.copy()
    new_run["run_log"] = log_msg
    new_run["environment_path"] = run_dir                                                                               # environment_path = workflow_url ?
    current_app.database.update_run(new_run)
    return new_run
