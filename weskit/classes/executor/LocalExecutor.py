#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
from __future__ import annotations

import logging
import subprocess  # nosec B603
from datetime import datetime
from os import PathLike
from typing import Optional

from builtins import int, super, open, property

import weskit.classes.executor.Executor as base
from weskit.classes.executor.ExecutorException import ExecutorException
from weskit.classes.ShellCommand import ShellCommand

logger = logging.getLogger(__name__)


class ClosingPopen(subprocess.Popen):
    """
    A decorator for Popen that ensured the stdin, stdout, and stderr file descriptors are
    closed, if the process is ended.

    Note: This is not a complete implementation. E.g. terminate() and signal() are not overridden.
    """

    def __init__(self, *args,
                 stdin=None,
                 stdout=None,
                 stderr=None,
                 **kwargs):
        self._stdin_fd = stdin
        self._stdout_fd = stdout
        self._stderr_fd = stderr
        super().__init__(*args, stdin=stdin, stdout=stdout, stderr=stderr, **kwargs)

    @property
    def stdin_fd(self):
        return self._stdin_fd

    @property
    def stderr_fd(self):
        return self._stderr_fd

    @property
    def stdout_fd(self):
        return self._stdout_fd

    def _close_std_fds(self):
        if self.stdin_fd is not None:
            self.stdin_fd.close()
        if self.stderr_fd is not None:
            self.stderr_fd.close()
        if self.stdout_fd is not None:
            self.stdout_fd.close()

    def poll(self):
        retcode = super().poll()
        if retcode is not None:
            self._close_std_fds()
        return retcode

    def wait(self, timeout: Optional[float] = ...) -> int:
        retcode = super().wait(timeout)
        self._close_std_fds()
        return retcode


class LocalExecutor(base.Executor):
    """
    Execute commands locally. The commands are executed asynchronously in the background managed
    by the operating system. Therefore, there is no asynchronous job management here.
    """

    def __init__(self):
        pass

    def execute(self,
                command: ShellCommand,
                stdout_file: Optional[PathLike] = None,
                stderr_file: Optional[PathLike] = None,
                stdin_file: Optional[PathLike] = None,
                settings: Optional[base.ExecutionSettings] = None) \
            -> base.ExecutedProcess:
        """
        Execute the process in the background and return the process ID.
        """
        if stdin_file is not None:
            stdin = open(stdin_file, "r")
        else:
            stdin = None
        if stderr_file is not None:
            stderr = open(stderr_file, "a")
        else:
            stderr = None
        if stdout_file is not None:
            stdout = open(stdout_file, "a")
        else:
            stdout = None

        start_time = datetime.now()

        # Note that shell=False (default) to ensure that no shell injection can be done.
        # The turned-off security warning for bandit is unavoidable, because we need to
        # execute an external command, here.
        # Note : ClosingPopen ensures that in most situations the stderr and stdin are closed,
        #        as soon as Popen.returncode is not None.
        try:
            process = ClosingPopen(command.command,
                                   cwd=command.workdir,
                                   stdout=stdout,
                                   stderr=stderr,
                                   stdin=stdin,
                                   env=command.environment,
                                   shell=False)
            logger.debug(f"Started process {process.pid}: {command.command}")

            return base.ExecutedProcess(command=command,
                                        executor=self,
                                        process_handle=process,
                                        pre_result=base.
                                        CommandResult(id=base.ProcessId(process.pid),
                                                      stdout_file=stdout_file,
                                                      stderr_file=stderr_file,
                                                      stdin_file=stdin_file,
                                                      run_status=base.RunStatus(),
                                                      start_time=start_time))
        except FileNotFoundError as e:
            raise ExecutorException(f"Invalid working directory '{command.workdir}", e)

    def get_status(self, process: base.ExecutedProcess) -> base.RunStatus:
        return base.RunStatus(process.handle.poll())

    def update_process(self, process: base.ExecutedProcess) -> base.ExecutedProcess:
        """
        Update the the executed process, if possible.
        """
        result = process.result
        return_code = process.handle.poll()
        if return_code is not None:
            result.status = base.RunStatus(return_code)
            result.end_time = datetime.now()
            process.result = result
        return process

    def kill(self, process: base.ExecutedProcess):
        process.handle.terminate()
        # TODO The API says little. The code says it uses os.kill for Unix. More recherche needed.

    def wait_for(self, process: base.ExecutedProcess, timeout: Optional[float] = None)\
            -> base.CommandResult:
        status = self.get_status(process)
        if not status.finished:
            logger.debug(f"Waiting for process {process.id}")
            process.handle.wait(timeout)
        return self.update_process(process).result