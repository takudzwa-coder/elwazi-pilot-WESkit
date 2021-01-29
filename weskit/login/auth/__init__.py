import hashlib
import time
import os
import yaml
from weskit.login.Users import User


class Local:

    def __init__(self, yamlfile="users.yaml", authtype='local'):
        self.credentialsFile = yamlfile
        self.lastupdate = 0
        self.dict = dict()
        self.dictUpdateLock = False
        self.authtype = authtype
        self.updateCredentials()

    def updateCredentials(self):
        if os.path.getmtime(self.credentialsFile) > self.lastupdate:
            print("*****************\nUpdate Local Users")
            self.lastupdate = os.path.getmtime(self.credentialsFile)
            if self.dictUpdateLock:
                while self.dictUpdateLock:
                    time.sleep(0.1)
            self.dictUpdateLock = True

            with open(self.credentialsFile, 'r') as stream:
                try:
                    print("Start Updating Local DB")
                    ystream = yaml.safe_load(stream)

                    self.dict = {
                        key: User(key, value, self.authtype)
                        for key, value in ystream.items() if
                        type(value) is dict and
                        len({
                            'roles',
                            'password',
                            'salt'}.intersection(value)) == 3
                        }

                    if(len(self.dict)) != len(ystream):
                        print(
                                ("Warning: Skiped %d Entrys from DBfile: "
                                    "Invalid Format!") % (
                                    len(ystream) - len(self.dict))
                        )
                except yaml.YAMLError as exc:
                    print(exc)
            self.dictUpdateLock = False
            print("End Updating LocalDB\n*****************")

    def authenticate(self, username, password):

        self.updateCredentials()
        if username not in self.dict:
            return(None)
        user = self.dict[username]

        if (hashlib.sha256((password+user.salt).encode('utf-8')).hexdigest() ==
                user.password):
            return(user)
        else:
            return (None)

    def get(self, username, default=None):
        self.updateCredentials()
        return (self.dict.get(username, default))
