#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

import logging

from flask import current_app, jsonify, request
from flask import Blueprint
from flask_jwt_extended import current_user

from weskit.api.utils import get_log_response, get_access_denied_response
from weskit.oidc.Decorators import login_required

bp = Blueprint("wes", __name__)


logger = logging.getLogger(__name__)


def _get_current_user_id():
    if current_app.is_login_enabled:
        return current_user.id
    else:
        return "not-logged-in-user"


@bp.route("/ga4gh/wes/v1/runs/<string:run_id>", methods=["GET"])
@login_required
def GetRunLog(run_id):
    try:
        logger.info("GetRun")
        run = current_app.manager.get_run(
            run_id=run_id, update=True)
        access_denied_response = get_access_denied_response(run_id, current_user.id, run)

        if access_denied_response is None:
            return {
                "run_id": run.run_id,
                "request": run.request,
                "state": run.run_status.name,
                "run_log": run.execution_log,
                "task_logs": run.task_logs,
                "outputs": run.outputs,
                "user_id": run.user_id
            }, 200
        else:
            return access_denied_response

    except Exception as e:
        logger.error(e, exc_info=True)
        raise e


@bp.route("/ga4gh/wes/v1/runs/<string:run_id>/cancel", methods=["POST"])
@login_required
def CancelRun(run_id):
    try:
        logger.info("CancelRun")
        run = current_app.manager.database.get_run(run_id)
        access_denied_response = get_access_denied_response(run_id, current_user.id, run)

        if access_denied_response is None:
            run = current_app.manager.cancel(run)
            logger.info("Run %s is canceled" % run_id)
            return {"run_id": run["run_id"]}, 200
        else:
            return access_denied_response

    except Exception as e:
        logger.error(e, exc_info=True)
        raise e


@bp.route("/ga4gh/wes/v1/runs/<string:run_id>/status", methods=["GET"])
@login_required
def GetRunStatus(run_id):
    try:
        logger.info("GetRunStatus")
        run = current_app.manager.get_run(run_id=run_id, update=True)
        access_denied_response = get_access_denied_response(run_id, current_user.id, run)

        if access_denied_response is None:
            return jsonify(run.run_status.name), 200
        else:
            return access_denied_response

    except Exception as e:
        logger.error(e, exc_info=True)
        raise e


@bp.route("/ga4gh/wes/v1/service-info", methods=["GET"])
def GetServiceInfo(*args, **kwargs):
    try:
        logger.info("GetServiceInfo")
        current_app.manager.update_runs(query={})
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
                current_app.service_info.
                get_default_workflow_engine_parameters(),
            "system_state_counts":
                current_app.manager.database.count_states(),
            "auth_instructions_url":
                current_app.service_info.get_auth_instructions_url(),
            "contact_info_url":
                current_app.service_info.get_contact_info_url(),
            "tags":
                current_app.service_info.get_tags()
        }
        return response, 200
    except Exception as e:
        logger.error(e, exc_info=True)
        raise e


@bp.route("/ga4gh/wes/v1/runs", methods=["GET"])
@login_required
def ListRuns(*args, **kwargs):
    try:
        logger.info("ListRuns")
        current_app.manager.update_runs(query={})
        user_id = _get_current_user_id()
        response = current_app.manager.database.list_run_ids_and_states()
        # filter for runs for this user
        response = [run for run in response if run["user_id"] == user_id]
        return jsonify(response), 200

    except Exception as e:
        logger.error(e, exc_info=True)
        raise e


@bp.route("/ga4gh/wes/v1/runs", methods=["POST"])
@login_required
def RunWorkflow():
    try:
        data = request.json
        logger.info("RunWorkflow")
        validator = current_app.request_validators["run_request"]
        validation_errors = validator.validate(
            data, require_workdir_tag=current_app.manager.require_workdir_tag)
        if len(validation_errors) > 0:
            return {
              "msg": "Malformed request: {}".format(validation_errors),
              "status_code": 400
            }, 400
        else:
            run = current_app.manager.create_and_insert_run(request=data,
                                                            user=_get_current_user_id())

            logger.info("Prepare execution")
            run = current_app.manager.\
                prepare_execution(run, files=request.files)
            current_app.manager.database.update_run(run)

            logger.info("Execute Workflow")
            run = current_app.manager.execute(run)
            current_app.manager.database.update_run(run)

            return jsonify({"run_id": run.run_id}), 200
    except Exception as e:
        logger.error(e, exc_info=True)
        raise e


@bp.route("/weskit/v1/runs", methods=["GET"])
@login_required
def ListRunsExtended(*args, **kwargs):
    try:
        logger.info("ListRunsExtended")
        current_app.manager.update_runs(query={})
        user_id = _get_current_user_id()
        response = current_app.manager.database.list_run_ids_and_states_and_times()

        # filter for runs for this user
        response = [run for run in response if run["user_id"] == user_id]

        return jsonify(response), 200
    except Exception as e:
        logger.error(e, exc_info=True)
        raise e


@bp.route("/weskit/v1/runs/<string:run_id>/stderr", methods=["GET"])
@login_required
def GetRunStderr(run_id):
    """
    Return a dictionary with a "content" field that contains the standard error of the requested
    run.
    """
    logger.info("GetStderr")
    return get_log_response(run_id, "stderr")


@bp.route("/weskit/v1/runs/<string:run_id>/stdout", methods=["GET"])
@login_required
def GetRunStdout(run_id):
    """
    Return a dictionary with a "content" field that contains the standard output of the requested
    run.
    """
    logger.info("GetStdout")
    return get_log_response(run_id, "stdout")
