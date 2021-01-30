import hashlib
import time
import os
import yaml
from weskit.login.Users import User
from typing import Union


class Local:

    def __init__(self, yamlfile: str = "users.yaml", authtype: str = 'local', logger=None) -> None:  # noqa: E501
        self.credentialsFile = yamlfile
        self.lastupdate = 0
        self.dict = dict()
        self.dictUpdateLock = False
        self.authtype = authtype

        # Setup default Logging
        self.logException = print
        self.logInfo = print
        self.logWarning = print

        # Specify custom Logger
        if logger:
            self.logException = logger.exception
            self.logInfo = logger.info
            self.logWarning = logger.warning

        # Load usercofig from file
        self.updateCredentials()

    def updateCredentials(self) -> None:
        # Avoid Thread colisons
        if self.dictUpdateLock:
            while self.dictUpdateLock:
                time.sleep(0.1)

        # Check if data in memory is up to date
        if os.path.getmtime(self.credentialsFile) > self.lastupdate:
            self.logInfo("********Update Local Users*********")
            self.lastupdate = os.path.getmtime(self.credentialsFile)

            # Protect class to be change by other thread
            self.dictUpdateLock = True

            with open(self.credentialsFile, 'r') as stream:
                try:
                    ystream = yaml.safe_load(stream)

                    # Copy only valid entries
                    self.dict = {
                        key: User(key, value, self.authtype)
                        for key, value in ystream.items() if
                        type(value) is dict and
                        len({
                            'roles',
                            'password',
                            'salt'}.intersection(value)) == 3
                        }

                    # Verify that File on disc has no corruped entries
                    if(len(self.dict)) != len(ystream):
                        self.logWarning(
                                ("Skiped %d Entrys from DBfile: "
                                    "Invalid Format!") % (
                                    len(ystream) - len(self.dict))
                        )
                    self.logInfo(
                        "Loaded %d users to backend %s !" %
                        (len(self.dict), self.authtype)
                    )

                except yaml.YAMLError as exc:
                    self.logException(exc)
            self.dictUpdateLock = False
            self.logInfo("********End Updating LocalDB*********")

    # Credentials return UserObject or None
    def authenticate(self, username: str, password: str) -> Union[User, None]:
        self.updateCredentials()
        if username not in self.dict:
            return(None)
        user = self.dict[username]

        if (hashlib.sha256((password+user.salt).encode('utf-8')).hexdigest() ==
                user.password):
            return(user)
        else:
            return (None)

    def get(self, username: str, default: User = None) -> Union[User, None]:
        # Get UserObject from AuthClass default return None
        self.updateCredentials()
        return (self.dict.get(username, default))
