#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

import logging

from flask import Blueprint
from flask import current_app, jsonify, request
from flask_jwt_extended import current_user

from weskit.api.Helper import Helper, run_log
from weskit.exceptions import ClientError
from weskit.oidc.Decorators import login_required
from weskit.api.RunStatus import RunStatus
from weskit.classes.ProcessingStage import ProcessingStage

bp = Blueprint("wes", __name__)


logger = logging.getLogger(__name__)


@bp.route("/ga4gh/wes/v1/runs/<string:run_id>", methods=["GET"])
@login_required()
def GetRunLog(run_id):
    logger.info("GetRun %s" % run_id)
    try:
        ctx = Helper(current_app, current_user)
        ctx.assert_run_id_syntax(run_id)
        manager = current_app.manager
        run = manager.update_run(manager.get_run(run_id))
        access_denied_response = ctx.get_access_denied_response(run_id, run)

        if access_denied_response is None:
            return run_log(run), 200
        else:
            return access_denied_response

    except ClientError as e:
        logger.warning(e, exc_info=True)
        return {"msg": e.message, "status_code": 500}, 500

    except Exception as e:
        logger.error(e, exc_info=True)
        raise e


@bp.route("/ga4gh/wes/v1/runs/<string:run_id>/cancel", methods=["POST"])
@login_required()
def CancelRun(run_id):
    logger.info("CancelRun %s" % run_id)
    try:
        ctx = Helper(current_app, current_user)
        ctx.assert_run_id_syntax(run_id)
        run = current_app.manager.get_run(run_id)
        access_denied_response = ctx.get_access_denied_response(run_id, run)

        if access_denied_response is None:
            run = current_app.manager.cancel(run)
            logger.info("Run %s is canceled" % run_id)
            return {"run_id": run["run_id"]}, 200
        else:
            return access_denied_response

    except ClientError as e:
        logger.warning(e, exc_info=True)
        return {"msg": e.message, "status_code": 500}, 500

    except Exception as e:
        logger.error(e, exc_info=True)
        raise e


@bp.route("/ga4gh/wes/v1/runs/<string:run_id>/status", methods=["GET"])
@login_required()
def GetRunStatus(run_id):
    logger.info("GetRunStatus %s" % run_id)
    try:
        ctx = Helper(current_app, current_user)
        ctx.assert_run_id_syntax(run_id)
        manager = current_app.manager
        run = manager.update_run(manager.get_run(run_id))
        access_denied_response = ctx.get_access_denied_response(run_id, run)

        if access_denied_response is None:
            return {
                "run_id": run_id,
                "state": RunStatus.from_stage(run.processing_stage, run.exit_code).name
            }, 200
        else:
            return access_denied_response

    except ClientError as e:
        logger.warning(e, exc_info=True)
        return {"msg": e.message, "status_code": 500}, 500

    except Exception as e:
        logger.error(e, exc_info=True)
        raise e


@bp.route("/ga4gh/wes/v1/service-info", methods=["GET"])
def GetServiceInfo(*args, **kwargs):
    logger.info("GetServiceInfo")
    try:
        current_app.manager.update_runs()
        response = {
            # Note that there is a deviation between the Swagger file and the model reported at
            # https://ga4gh.github.io/workflow-execution-service-schemas/docs
            # This latter version seems to fit to no file in the repository (e.g. no "organization"
            # field is mentioned anywhere in the repository!). Furthermore, the Swagger is used to
            # autogenerate client APIs. Therefore, we consider the Swagger to represent the
            # standard

            # "id":
            #     current_app.service_info.id(),
            # "name":
            #     current_app.service_info.name(),
            # "type":
            #     current_app.service_info.type(),
            # "description":
            #     current_app.service_info.description(),
            # "organization":
            #     current_app.service_info.organization(),
            # "documentationUrl":
            #     current_app.service_info.documentation_url(),
            "contact_info_url":
                current_app.service_info.contact_url(),
            # "createdAt":
            #     rfc3339(current_app.service_info.created_at()),
            # "updatedAt":
            #     rfc3339(current_app.service_info.updated_at()),
            "workflow_type_versions":
                current_app.service_info.workflow_type_versions(),
            "supported_wes_versions":
                current_app.service_info.supported_wes_versions(),
            "supported_filesystem_protocols":
                current_app.service_info.supported_filesystem_protocols(),
            "workflow_engine_versions":
                current_app.service_info.workflow_engine_versions(),
            "default_workflow_engine_parameters":
                current_app.service_info.default_workflow_engine_parameters(),
            "system_state_counts":
                current_app.service_info.system_state_counts(),
            "auth_instructions_url":
                current_app.service_info.auth_instructions_url(),
            "tags":
                current_app.service_info.tags()
        }
        return response, 200
    except Exception as e:
        logger.error(e, exc_info=True)
        raise e


@bp.route("/ga4gh/wes/v1/runs", methods=["GET"])
@login_required()
def ListRuns(*args, **kwargs):
    logger.info("ListRuns")
    try:
        ctx = Helper(current_app, current_user)
        current_app.manager.update_runs()
        runs = [{
            "run_id": str(run_info["id"]),
            "state": RunStatus.from_stage(ProcessingStage.from_string(run_info["processing_stage"]),
                                          run_info["exit_code"]).name
        } for run_info in current_app.manager.database.list_run_ids_and_stages(ctx.user.id)]
        return jsonify({
            "runs": runs,
            "next_page_token": ""
        }), 200
    except Exception as e:
        logger.error(e, exc_info=True)
        raise e


@bp.route("/ga4gh/wes/v1/runs", methods=["POST"])
@login_required()
def RunWorkflow(*args, **kwargs):
    logger.info("RunWorkflow")
    try:
        ctx = Helper(current_app, current_user)
        data = request.form.to_dict()
        if len(data) == 0:
            return {
                "msg": "Malformed request: Empty form data",
                "status_code": 400
            }, 400

        validator = current_app.request_validators["run_request"]
        validation_result = validator.validate(data)
        logger.debug(f"Validation result = {validation_result}")
        if isinstance(validation_result, list):
            return {
                "msg": "Malformed request: {}".format(validation_result),
                "status_code": 400
            }, 400
        else:
            run = current_app.manager.\
                create_and_insert_run(validated_request=validation_result,
                                      user_id=ctx.user.id)
            logger.info("Created run %s" % run.id)

        logger.info("Preparing execution %s" % run.id)
        run = current_app.manager.\
            prepare_execution(run, files=request.files)
        run = current_app.manager.database.update_run(run)

        logger.info("Executing Workflow %s" % run.id)
        run = current_app.manager.execute(run)
        run = current_app.manager.database.update_run(run)

        return {"run_id": run.id}, 200

    except ClientError as e:
        logger.warning(e, exc_info=True)
        return {"msg": e.message, "status_code": 500}, 500
    except Exception as e:
        logger.error(e, exc_info=True)
        raise e


@bp.route("/weskit/v1/runs", methods=["GET"])
@login_required()
def ListRunsExtended(*args, **kwargs):
    logger.info("ListRunsExtended")
    try:
        ctx = Helper(current_app, current_user)
        current_app.manager.update_runs()
        response = current_app.manager.database.\
            list_run_ids_and_stages_and_times(ctx.user.id)
        return jsonify(response), 200
    except Exception as e:
        logger.error(e, exc_info=True)
        raise e


@bp.route("/weskit/v1/runs/<string:run_id>/stderr", methods=["GET"])
@login_required()
def GetRunStderr(run_id):
    """
    Return a dictionary with a "content" field that contains the standard error of the requested
    run.
    """
    try:
        ctx = Helper(current_app, current_user)
        logger.info("GetStderr %s" % run_id)
        ctx.assert_run_id_syntax(run_id)
        return ctx.get_log_response(run_id, "stderr")
    except Exception as e:
        logger.error(e, exc_info=True)
        raise e


@bp.route("/weskit/v1/runs/<string:run_id>/stdout", methods=["GET"])
@login_required()
def GetRunStdout(run_id):
    """
    Return a dictionary with a "content" field that contains the standard output of the requested
    run.
    """
    try:
        ctx = Helper(current_app, current_user)
        logger.info("GetStdout %s" % run_id)
        ctx.assert_run_id_syntax(run_id)
        return ctx.get_log_response(run_id, "stdout")
    except Exception as e:
        logger.error(e, exc_info=True)
        raise e
