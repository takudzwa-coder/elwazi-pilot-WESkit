#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
import subprocess   # nosec B603
from builtins import int, super, open, property, bool
from os import PathLike
from typing import Optional

import weskit.classes.command_executor.Executor as base
from weskit.classes.ShellCommand import ShellCommand
from weskit.utils import get_current_timestamp


class LocalProcessId(base.ExecutorProcessId):
    """
    Unix process IDs are integers in the range (0, 65535).
    """
    def __init__(self, value: int):
        super().__init__(value)


class ExecutedProcess(base.ExecutedProcess):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def handle(self) -> subprocess.Popen:
        return super().handle

    def process_id(self) -> LocalProcessId:
        return LocalProcessId(self._process_handle.pid)


class RunStatus(base.RunStatus):

    def __init__(self, value: Optional[int] = None):
        super().__init__(value)

    @property
    def finished(self) -> bool:
        return self.value is not None

    @property
    def success(self) -> bool:
        return self.value is not None and self.value == 0

    @property
    def failed(self) -> bool:
        return self.value is not None and self.value != 0


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

    def submit(self,
               command: ShellCommand,
               stdout_file: PathLike,
               stderr_file: PathLike,
               settings: Optional[base.ExecutionSettings] = None) \
            -> base.ExecutedProcess:
        """
        Execute the process in the background and return the process ID.
        """
        stderr = open(stderr_file, "a")
        stdout = open(stdout_file, "a")

        start_time = get_current_timestamp()

        # Note that shell=False (default) to ensure that no shell injection can be done.
        # The turned-off security warning for bandit is unavoidable, because we need to
        # execute an external command, here.
        # Note : ClosingPopen ensures that in most situations the stderr and stdin are closed,
        #        as soon as Popen.returncode is not None.
        process = ClosingPopen(command.command,
                               cwd=command.workdir,
                               stdout=stdout,
                               stderr=stderr,
                               env=command.environment,
                               shell=False)

        return ExecutedProcess(command=command,
                               executor=self,
                               process_handle=process,
                               pre_result=base.CommandResult(id=LocalProcessId(process.pid),
                                                             stdout_file=stdout_file,
                                                             stderr_file=stderr_file,
                                                             run_status=RunStatus(),
                                                             start_time=start_time))

    def get_status(self, process: ExecutedProcess) -> RunStatus:
        return RunStatus(process.handle.poll())

    def update_process(self, process: ExecutedProcess) -> ExecutedProcess:
        """
        Update the the executed process, if possible.
        """
        result = process.result
        return_code = process.handle.poll()
        if return_code is not None:
            result.status = RunStatus(return_code)
            result.end_time = get_current_timestamp()
        process.result = result
        return process

    def kill(self, process: ExecutedProcess) -> bool:
        process.handle.terminate()
        # TODO The API says little. The code says it uses os.kill for Unix. More recherche needed.
        return True

    def wait_for(self, process: ExecutedProcess, timeout: Optional[float] = None)\
            -> base.CommandResult:
        status = self.get_status(process)
        if not status.finished:
            process.handle.wait(timeout)
        return self.update_process(process).result
