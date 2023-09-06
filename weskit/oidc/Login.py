# Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
# SPDX-FileCopyrightText: 2023 2023 The WESkit Team
#
# SPDX-License-Identifier: MIT

class Login:

    def __init__(self,
                 realm: str,
                 client_id: str,
                 client_secret: str,
                 oidc_config: dict):
        self.realm = realm
        self.client_id = client_id
        self.client_secret = client_secret
        self.config = oidc_config

    @property
    def introspection_endpoint(self) -> str:
        return self.config["introspection_endpoint"]

    @property
    def token_endpoint(self) -> str:
        return self.config["token_endpoint"]

    @property
    def userinfo_endpoint(self) -> str:
        return self.config["userinfo_endpoint"]
