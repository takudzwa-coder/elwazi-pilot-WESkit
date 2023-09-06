# Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
# SPDX-FileCopyrightText: 2023 2023 The WESkit Team
#
# SPDX-License-Identifier: MIT

class WESkitError(Exception):

    def __init__(self, message, *args):
        """
        :param message: Used as message in the REST response.
        """
        super().__init__(message, *args)
    #     self._message = message

    @property
    def message(self):
        return self.args[0]


class ClientError(WESkitError):
    """
    A class for errors caused by the REST client. These errors are reported back to the REST client
    and should not compromise internal data.
    """
    pass


class DatabaseOperationError(WESkitError):
    pass


class ConcurrentModificationError(DatabaseOperationError):
    """
    Raised if a database modification was attempted, but the value in the database has been updated
    concurrently since the original was retrieved.
    """

    def __init__(self, expected_version, attempted_value, db_value):
        self._message = "Update failed due to concurrent modification. " +\
                        f"Expected db_version={expected_version}:\n" +\
                        "\t" + str(attempted_value) + " and " +\
                        "\t" + str(db_value)
        self._attempted_value = attempted_value
        self._db_value = db_value

    @property
    def attempted_value(self):
        """
        The value that was tried to be written to the database.
        """
        return self._attempted_value

    @property
    def db_value(self):
        """
        The value found in the database. If this is None, no value was set (e.g. no possible match
        was searched for to create the exception). Otherwise, a values from the database, that
        should have been replaced, but wasn't because of a concurrent modification.
        """
        return self._db_value
