# Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
# SPDX-FileCopyrightText: 2023 2023 The WESkit Team
#
# SPDX-License-Identifier: MIT

class ExecutorError(Exception):
    """
    Any error in the Executor, including e.g. parse errors, etc.
    """
    pass


class RetryableExecutorError(Exception):
    """
    Any error that is retryable like get_status
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
