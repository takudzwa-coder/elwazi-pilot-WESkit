import logging
from weskit.classes.Run import Run


logger = logging.getLogger(__name__)


def get_access_denied_response(run_id: str,
                               user_id: str,
                               run: Run = None):
    if run is None:
        logger.error("Could not find %s" % run_id)
        return {"msg": "Could not find %s" % run_id,
                "status_code": 0
                }, 404

    if user_id != run.user_id:
        logger.error("User not allowed to perform this action on %s" % run_id)
        return {"msg": "User not allowed to perform this action on %s" % run_id,
                       "status_code": 0}, 403

    return None
