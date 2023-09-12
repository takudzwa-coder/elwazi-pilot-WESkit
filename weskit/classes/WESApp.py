#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2023 The WESkit Team
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from logging import Logger

from typing import Optional, cast

from flask import Flask

from weskit.classes.Manager import Manager
from weskit.api.ServiceInfo import ServiceInfo
from weskit.oidc.Login import Login


class WESApp(Flask):
    """We make a subclass of Flask that takes the important app-global
    (~thread local) resources.
    Compare https://stackoverflow.com/a/21845744/8784544"""

    def __init__(self,
                 manager: Manager,
                 service_info: ServiceInfo,
                 request_validators: dict,
                 logger: Logger,
                 log_config: dict,
                 is_login_enabled: bool = True,
                 oidc_login: Optional[Login] = None,
                 *args, **kwargs):
        super(WESApp, self).__init__(__name__, *args, **kwargs)
        self._manager: Manager = manager
        self._service_info = service_info
        self._request_validators = request_validators
        self._is_login_enabled = is_login_enabled
        self._oidc_login = oidc_login
        self._log_config = log_config
        self.logger = logger

    @property
    def manager(self) -> Manager:
        return self._manager

    @property
    def service_info(self) -> ServiceInfo:
        return self._service_info

    @property
    def request_validators(self) -> dict:
        return self._request_validators

    @property
    def is_login_enabled(self) -> bool:
        return self._is_login_enabled

    @is_login_enabled.setter
    def is_login_enabled(self, value: bool = True):
        self._is_login_enabled = value

    @property
    def oidc_login(self) -> Optional[Login]:
        return self._oidc_login

    @oidc_login.setter
    def oidc_login(self, value: Login):
        self._oidc_login = value

    @property
    def log_config(self) -> dict:
        return self._log_config

    @staticmethod
    def from_current_app(app: Flask) -> WESApp:
        """
        There is an issue related to typing with mypy that essentially leaves the problem unsolved:

            https://github.com/pallets/flask/issues/4073

        I centralized this trivial code here to allows tracking the places where this workaround
        is used.
        """
        return cast(WESApp, app)
