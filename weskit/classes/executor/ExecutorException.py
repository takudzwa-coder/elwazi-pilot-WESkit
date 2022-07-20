#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

class ExecutorException(Exception):
    """
    Any error in the Executor, including e.g. parse errors, etc.
    """
    pass


class ExecutionError(ExecutorException):
    """
    Error during the execution of a command, i.e. command returned e.g. with exit code != 0.
    """
    pass


class TimingError(ExecutorException):
    """
    Command execution was partially successful i.e. command execution returned no output
    """
    pass


class ConnectionError(ExecutorException):
    """
    A connection error prevented the operation to succeed. This should be used e.g. if channels
    cannot be opened or connections are interrupted.
    """
    pass
