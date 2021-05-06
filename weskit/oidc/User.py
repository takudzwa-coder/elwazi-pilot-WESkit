from flask_jwt_extended import utils


class User:
    """
    This class makes the content of the jwt easily accessible.
    """
    def __init__(self):
        token_data = utils.get_raw_jwt()
        self.id = token_data.get('sub', None)
        self.username = token_data.get('name', None)
        self.email_verified = token_data.get('email_verified', None)
        self.preferred_username = token_data.get('preferred_username', None)
        self.email = token_data.get('email', None)
        # self.user_claims = tokenData.get('user_claims', None)
        self.auth_time = token_data.get('auth_time', None)
        self.realm_roles = token_data.get('realm_access', dict()).get('roles', [])
