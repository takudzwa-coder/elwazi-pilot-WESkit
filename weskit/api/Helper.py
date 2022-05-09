#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

import logging
from typing import Optional

from weskit.oidc.User import User
from weskit.ClientError import ClientError
from weskit import WESApp
from weskit.api.RunRequestValidator import RunRequestValidator
from weskit.classes.RunStatus import RunStatus
from weskit.classes.Run import Run


logger = logging.getLogger(__name__)


class Helper:
    """
    Service that groups helper functions that need access to current_app and current_user. This
    allows for better testing.
    """

    def __init__(self, current_app: WESApp, current_user: Optional[User]):
        self.app = current_app

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
        run = self.app.manager.get_run(
            run_id=run_id, update=True)
        access_denied_response = self.get_access_denied_response(run_id, run)

        if access_denied_response is None:
            if run.status is not RunStatus.COMPLETE:
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
