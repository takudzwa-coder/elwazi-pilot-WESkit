from weskit.login import auth

# This dictionary is initialized at loading the module
# It contains all login methods
authObjDict ={'local':auth.Local("users.yaml",'local')}

