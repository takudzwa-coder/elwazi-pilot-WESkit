from flask_jwt_extended import utils


class User:
    """
    This class makes the content of the jwt easily accessible.
    """
    def __init__(self):
        tokenData = utils.get_raw_jwt()
        self.id = tokenData.get('sub', None)
        self.username = tokenData.get('name', None)
        self.email_verified = tokenData.get('email_verified', None)
        self.preferred_username = tokenData.get('preferred_username', None)
        self.email = tokenData.get('email', None)
        #self.user_claims = tokenData.get('user_claims', None)
        self.auth_time = tokenData.get('auth_time', None)
        self.realm_roles = tokenData.get('realm_access', dict()).get('roles', [])

