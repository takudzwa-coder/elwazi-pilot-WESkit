#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

class ClientError(Exception):
    """
    A class for errors caused by the REST client. These errors are reported back to the REST client
    and should not compromise internal data.
    """

    def __init__(self, message):
        """
        :param message: Used as message in the REST response.
        """
        self.message = message

    def __str__(self):
        return "%s: %s" % (self.__class__.__name__, self.message)
