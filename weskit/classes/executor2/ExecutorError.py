# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

class ExecutorError(Exception):
    """
    Any error in the Executor, including e.g. parse errors, etc.
    """
    pass


class RetryableExecutorError(ExecutorError):
    """
    Any error that is retryable.
    """
    pass


class NonRetryableExecutorError(ExecutorError):
    """
    A non-retryable error.
    """
    pass


class TimeoutError(ExecutorError):
    """
    Command was executed but no response was observed after exceeding the given timeout.
    """
    pass


class ConnectionError(ExecutorError):
    """
    A connection error prevented the operation to succeed. This should be used e.g. if channels
    cannot be opened or connections are interrupted.
    """
    pass
