from flask import current_app, jsonify, request
from flask import Blueprint


bp = Blueprint("wes", __name__)


@bp.route("/ga4gh/wes/v1/runs/<string:run_id>", methods=["GET"])
def GetRunLog(run_id):
    current_app.logger.info("GetRun")
    run = current_app.manager.get_run(
        run_id=run_id, database=current_app.database, update=True)
    if run is None:
        current_app.error_logger.error("Could not find %s" % run_id)
        return {"msg": "Could not find %s" % run_id,
                "status_code": 0
                }, 404
    else:
        return run.get_run_log(), 200


@bp.route("/ga4gh/wes/v1/runs/<string:run_id>/cancel", methods=["POST"])
def CancelRun(run_id):
    current_app.logger.info("CancelRun")
    run = current_app.database.get_run(run_id)
    if run is None:
        current_app.error_logger.error("Could not find %s" % run_id)
        return {"msg": "Could not find %s" % run_id,
                "status_code": 0
                }, 404
    else:
        run = current_app.manager.cancel(run, current_app.database)
        current_app.logger.info("Run %s is canceled" % run_id)
        return {k: run[k] for k in ["run_id"]}, 200


@bp.route("/ga4gh/wes/v1/runs/<string:run_id>/status", methods=["GET"])
def GetRunStatus(run_id):
    current_app.logger.info("GetRunStatus")
    run = current_app.manager.get_run(
        run_id=run_id, database=current_app.database, update=True)
    if run is None:
        current_app.error_logger.error("Could not find %s" % run_id)
        return jsonify({"msg": "Could not find %s" % run_id,
                        "status_code": 0}), 404
    else:
        return jsonify(run.run_status), 200


@bp.route("/ga4gh/wes/v1/service-info", methods=["GET"])
def GetServiceInfo(*args, **kwargs):
    current_app.logger.info("GetServiceInfo")
    current_app.manager.update_runs(
        database=current_app.database,
        query={})
    response = {
        "workflow_type_versions":
            current_app.service_info.get_workflow_type_versions(),
        "supported_wes_versions":
            current_app.service_info.get_supported_wes_versions(),
        "supported_filesystem_protocols":
            current_app.service_info.get_supported_filesystem_protocols(),
        "workflow_engine_versions":
            current_app.service_info.get_workflow_engine_versions(),
        "default_workflow_engine_parameters":
            current_app.service_info.get_default_workflow_engine_parameters(),
        "system_state_counts":
            current_app.database.count_states(),
        "auth_instructions_url":
            current_app.service_info.get_auth_instructions_url(),
        "contact_info_url":
            current_app.service_info.get_contact_info_url(),
        "tags":
            current_app.service_info.get_tags()
    }
    return jsonify(response), 200


@bp.route("/ga4gh/wes/v1/runs", methods=["GET"])
def ListRuns(*args, **kwargs):
    current_app.logger.info("ListRuns")
    current_app.manager.update_runs(current_app.database, query={})
    response = current_app.database.list_run_ids_and_states()
    return jsonify(response), 200


@bp.route("/ga4gh/wes/v1/runs", methods=["POST"])
def RunWorkflow():
    data = request.form
    current_app.logger.info("RunWorkflow")

    run = current_app.manager.create_and_insert_run(
        request=data,
        database=current_app.database)

    current_app.logger.info("Prepare execution")
    run = current_app.manager.prepare_execution(run, files=request.files)
    current_app.database.update_run(run)

    current_app.logger.info("Execute Workflow")
    run = current_app.manager.execute(run)
    current_app.database.update_run(run)

    return jsonify({"run_id": run.run_id}), 200
