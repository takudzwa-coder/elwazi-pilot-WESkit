#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

from flask_jwt_extended import utils


class User:
    """
    This class makes the content of the jwt easily accessible.
    """

    not_logged_in_user_id = "not-logged-in-user"

    def __init__(self):
        token_data = utils.get_raw_jwt()
        self.id = token_data.get('sub', User.not_logged_in_user_id)
        self.username = token_data.get('name', None)
        self.email_verified = token_data.get('email_verified', None)
        self.preferred_username = token_data.get('preferred_username', None)
        self.email = token_data.get('email', None)
        # self.user_claims = tokenData.get('user_claims', None)
        self.auth_time = token_data.get('auth_time', None)
        self.realm_roles = token_data.get('realm_access', dict()).get('roles', [])
