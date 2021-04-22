from flask import current_app


import requests

from flask_jwt_extended.view_decorators import _decode_jwt_from_headers
from typing import Optional
import logging


def onlineValidation() -> bool:
    """
    checks the validity of a token with a request to OIDC provider.
    Returns True if cookie is valid and false if session ended.
    """
    logger = logging.getLogger(__name__)
    app = current_app

    access_token = getToken()
    payload = {
        "client_id": app.OIDC_Login.client_id,
        "client_secret": app.OIDC_Login.client_secret,
        "token": access_token
    }
    try:
        # Make request
        j = requests.post(
            data=payload,
            url=app.OIDC_Login.oidc_config["introspection_endpoint"]
        ).json()

    except Exception as e:
        logger.exception(
            "Could not reach OIDC provider for online Validation"
        )
        logger.exception(e)

        return False

    return j.get('active', False)


def getToken(token_type: str = "access") -> Optional[str]:
    """
    This function returns the encoded access_token from different sources.
    Its basically identical to a function from jwt_extended but has different
    return
    """

    try:
        encoded_token, csrf_token = _decode_jwt_from_headers()
        return encoded_token

    except Exception:
        # If Token is not in header
        return None
    return None
