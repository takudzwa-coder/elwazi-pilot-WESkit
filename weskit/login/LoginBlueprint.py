from flask import jsonify, request, render_template, Blueprint
from flask_jwt_extended import (
    jwt_refresh_token_required,
    # get_jwt_identity,
    current_user
)

from weskit import login as auth

login = Blueprint('login', __name__, template_folder='templates')


###########################################################
#               Login / Logout / Tokenrenew               #
###########################################################

##########################################
#  Authenticate User (POST JSON or FORM  #
##########################################

@login.route('/login', methods=['POST'])
def authenticateUser():
    return(auth.login(request))


##########################################
#  Show Login Web Page                   #
##########################################
@login.route('/login', methods=['GET'])
def authenticateUserHTML():
    return(
        render_template(
            'loginForm.html',
            hideHint="hidden"
            )
        )


@login.route('/', methods=['GET'])
def authenticateUserHTMLtop():
    return(render_template('loginForm.html', hideHint="hidden"))


#########################################
#  Submit POST to get new access Token  #
#########################################

@login.route('/refresh', methods=['POST'])
@jwt_refresh_token_required
def refresh():
    return(auth.refresh())


########################################
#  Logout via GET or POST              #
########################################

@login.route('/logout', methods=['GET', 'POST'])
def logout():
    return (auth.logout())


###############################################################
#               Get description of user                       #
###############################################################

@login.route('/ga4gh/wes/user_status', methods=['GET'])
@auth.login_required
def protected():
    # username = get_jwt_identity()
    return jsonify({
        'currentUser': '{}'.format(current_user.username),
        'UserRoles': '{}'.format(current_user.roles),
        'Current authmethod': '{}'.format(current_user.authType)
        }), 200
