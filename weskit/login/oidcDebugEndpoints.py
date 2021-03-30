from weskit.login.Login import AutoLoginUser
from flask_jwt_extended import current_user
from flask import Blueprint
bp = Blueprint('loginTestEndpoints', __name__, template_folder='templates')


# Add demo Login for Dashboard
@bp.route("/login/test", methods=['GET'])
@AutoLoginUser
def auto_login_test():
    response = """
    If you see this page the login was successful. <br>
    You are:<br>
    id: {}<br>
    username: {}<br>
    email_verified: {}<br>
    preferred_username: {}<br>
    email: {}<br>
    realm_roles: {}<br>
    auth_time: {}<br>
    """.format(
        current_user.id,
        current_user.username,
        current_user.email_verified,
        current_user.preferred_username,
        current_user.email,
        current_user.realm_roles,
        current_user.auth_time
    )
    return response, 200
