# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

import logging
from typing import Optional

from weskit.api.RunRequestValidator import RunRequestValidator
from weskit.classes.Run import Run
from weskit.api.RunStatus import RunStatus
from weskit.classes.WESApp import WESApp
from weskit.exceptions import ClientError
from weskit.oidc.User import User

logger = logging.getLogger(__name__)


class Helper:
    """
    Service that groups helper functions that need access to current_app and current_user. This
    allows for better testing.
    """

    def __init__(self, current_app: WESApp, current_user: Optional[User]):
        self.app: WESApp = current_app

        if current_user is None or current_user == None:   # noqa E711
            # Python sucks. current_user can be (some) None, but still
            # `current_user is None == False`.
            self.user = User()
        else:
            self.user = current_user

    def get_access_denied_response(self,
                                   run_id: str,
                                   run: Optional[Run] = None):
        if run is None:
            logger.error("Could not find '%s'" % run_id)
            return {"msg": "Could not find '%s'" % run_id,
                    "status_code": 404
                    }, 404     # NOT FOUND

        if self.user.id != run.user_id:
            logger.error("User '%s' not allowed to access '%s'" %
                         (self.user.id, run_id))
            return {"msg": "User '%s' not allowed to access '%s'" % (self.user.id, run_id),
                    "status_code": 403
                    }, 403     # FORBIDDEN

        return None

    def get_log_response(self, run_id: str, log_name: str):
        """
        Safe access to "stderr" or "stdout" (= log_name) data.
        """
        manager = self.app.manager
        run = manager.get_run(run_id)
        if run is None:
            raise RuntimeError(f"Could not find run with identifier {run_id}")
        else:
            run = manager.update_run(run)
        access_denied_response = self.get_access_denied_response(run_id, run)

        if access_denied_response is None:
            run_ga4gh_status = RunStatus.from_stage(run.processing_stage)
            if run_ga4gh_status is not RunStatus.COMPLETE:
                return {"msg": "Run '%s' is not in COMPLETED state" % run_id,
                        "status_code": 409
                        }, 409     # CONFLICT (with current resource state)
            else:
                return {"content": getattr(run, log_name)}, 200
        else:
            return access_denied_response

    def assert_user_id(self, user_id: str):
        msg = RunRequestValidator.invalid_user_id(user_id)
        if msg:
            raise ClientError("Syntactically invalid user ID: '%s'" % user_id)

    def assert_run_id_syntax(self, run_id: str):
        msg = RunRequestValidator.invalid_run_id(run_id)
        if msg:
            raise ClientError("Syntactically invalid run ID: '%s'" % run_id)


def run_log(run: Run) -> dict:
    run_ga4gh_status = RunStatus.from_stage(run.processing_stage).name
    return {
        "run_id": run.id,
        "request": run.request,
        "state": run_ga4gh_status,
        "run_log": execution_log_to_run_log(run),
        "task_logs": run.task_logs,
        "outputs": run.outputs,
        "user_id": run.user_id
    }


def execution_log_to_run_log(run: Run) -> dict:
    return {
        # It is not clear from the documentation or discussion what the "workflow name" should be
        # We use the path to the workflow file (workflow_url) for now.
        "name": run.request.get("workflow_url", None),
        "cmd": run.execution_log.get("cmd", None),
        "start_time": run.execution_log.get("start_time", None),
        "end_time": run.execution_log.get("end_time", None),
        "stdout": run.execution_log.get("stdout_file", None),
        "stderr": run.execution_log.get("stderr_file", None),
        "exit_code": run.execution_log.get("exit_code", None)
    }
