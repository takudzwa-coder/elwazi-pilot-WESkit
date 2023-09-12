# SPDX-FileCopyrightText: 2023 The WESkit Team
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Dict, Set, Any

from flask import Flask

not_logged_in_user_id = "not-logged-in-user"


@dataclass
class User:
    """
    This class makes the content of the jwt easily accessible.
    """
    id: str = not_logged_in_user_id
    username: Optional[str] = None
    email_verified: Optional[str] = None
    preferred_username: Optional[str] = None
    email: Optional[str] = None
    auth_time: Optional[str] = None
    realm_roles: dict = field(default_factory=lambda: {"roles": []})

    @staticmethod
    def from_jwt_payload(app: Flask, jwt_payload: Dict[Any, Any]) -> User:
        """
        Create User object from jwt_payload dictionary. Only fields that can be processed are
        mapped into the User instance. Other fields are ignored.

        :param app: Flask application object
        :param jwt_payload: Dictionary with the JWT payload as received from the client.
        :return:
        """
        identity_claim = app.config["JWT_IDENTITY_CLAIM"]
        key_mapping = {
            identity_claim: "id",
            "name": "username",
            "realm_access": "realm_roles"
        }
        allowed_fields: Set[str] = {
            identity_claim, "name", "realm_access", "email_verified", "preferred_username",
            "email", "auth_time"
        }
        return User(**{
            key_mapping.get(k, k): v
            for k, v in jwt_payload.items()
            if k in allowed_fields
        })
