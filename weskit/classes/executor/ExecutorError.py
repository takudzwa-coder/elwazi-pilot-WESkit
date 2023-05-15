#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

class ExecutorError(Exception):
    """
    Any error in the Executor, including e.g. parse errors, etc.
    """
    pass


class WorkLoadError(ExecutorError):
    """
    Error during the execution of a command, i.e. command returned e.g. with exit code != 0.
    """
    pass


class TimeoutError(ExecutorError):
    """
    Command was executed but no response was observed after exceeding the given timeout
    """
    pass


class ConnectionError(ExecutorError):
    """
    A connection error prevented the operation to succeed. This should be used e.g. if channels
    cannot be opened or connections are interrupted.
    """
    pass
