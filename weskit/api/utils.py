#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

import logging

from flask import current_app, jsonify
from flask_jwt_extended import current_user

from weskit.classes.RunStatus import RunStatus
from weskit.classes.Run import Run


logger = logging.getLogger(__name__)


def _get_current_user_id():
    if current_app.is_login_enabled:
        return current_user.id
    else:
        return "not-logged-in-user"


def get_access_denied_response(run_id: str,
                               user_id: str,
                               run: Run = None):
    if run is None:
        logger.error("Could not find '%s'" % run_id)
        return {"msg": "Could not find '%s'" % run_id,
                "status_code": 404
                }, 404     # NOT FOUND

    if user_id != run.user_id:
        logger.error("User not allowed to perform this action on '%s'" % run_id)
        return {"msg": "User not allowed to perform this action on '%s'" % run_id,
                "status_code": 403
                }, 403     # FORBIDDEN

    return None


def get_log_response(run_id: str, log_name: str):
    """
    Safe access to "stderr" or "stdout" (= log_name) data.
    """
    try:
        run = current_app.manager.get_run(
            run_id=run_id, update=True)
        access_denied_response = get_access_denied_response(run_id, _get_current_user_id(), run)

        if access_denied_response is None:
            if run.run_status is not RunStatus.COMPLETE:
                return {"msg": "Run '%s' is not in COMPLETED state" % run_id,
                        "status_code": 409
                        }, 409     # CONFLICT (with current resource state)
            else:
                return jsonify({"content": getattr(run, log_name)}), 200
        else:
            return access_denied_response

    except Exception as e:
        logger.error(e, exc_info=True)
        raise e
