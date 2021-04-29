import requests
from flask_jwt_extended.view_decorators import _decode_jwt_from_headers
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def online_validation(app) -> bool:
    """
    Checks the validity of a token with a request to OIDC provider.
    Returns True if cookie is valid and false if session ended.
    """
    access_token = get_token()
    payload = {
        "client_id": app.oidc_login.client_id,
        "client_secret": app.oidc_login.client_secret,
        "token": access_token
    }
    try:
        j = requests.post(
            data=payload,
            url=app.oidc_login.introspection_endpoint
        ).json()

    except Exception as e:
        logger.exception("Could not reach OIDC provider for online validation")
        logger.exception(e)
        return False

    return j.get('active', False)


def get_token(token_type: str = "access") -> Optional[str]:
    """
    This function returns the encoded access_token from different sources.
    Its basically identical to a function from jwt_extended but has different
    return
    """

    try:
        encoded_token, csrf_token = _decode_jwt_from_headers()
    except Exception:  # TODO Check: Can this be InvalidHeaderError?
        # If Token is not in header
        encoded_token = None
    return encoded_token
