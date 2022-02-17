#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
import logging
import os
import subprocess  # nosec B603
from datetime import datetime
from os import PathLike
from pathlib import Path
from shutil import copyfile
from typing import Optional, cast, IO

from builtins import int, super, open, property

import weskit.classes.executor.Executor as base
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

    def wait(self, timeout: Optional[float] = None) -> int:
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

    def _file_repr_to_io(self, file: Optional[base.FileRepr], mode: str) -> Optional[IO]:
        if isinstance(file, PathLike):
            return open(cast(PathLike, file), mode)
        else:
            return file

    def execute(self,
                command: ShellCommand,
                stdout_file: Optional[base.FileRepr] = None,
                stderr_file: Optional[base.FileRepr] = None,
                stdin_file: Optional[base.FileRepr] = None,
                settings: Optional[base.ExecutionSettings] = None,
                **kwargs) \
            -> base.ExecutedProcess:
        """
        Execute the process in the background and return the process ID.

        Note, the LocalExecutor supports processing of IOBase objects as stderr, stdout, stdin.
        """
        # In the following explicit cast is used to avoid mypy errors. Mypy cannot (yet) infer the
        # type from `isinstance` conditions.
        stdin = self._file_repr_to_io(stdin_file, "r")
        stderr = self._file_repr_to_io(stderr_file, "a")
        stdout = self._file_repr_to_io(stdout_file, "a")
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
                                   shell=False,
                                   **kwargs)
            logger.debug(f"Started process {process.pid}: {command.command}")

            return base.ExecutedProcess(executor=self,
                                        process_handle=process,
                                        pre_result=base.
                                        CommandResult(command=command,
                                                      id=base.ProcessId(process.pid),
                                                      stdout_file=stdout_file,
                                                      stderr_file=stderr_file,
                                                      stdin_file=stdin_file,
                                                      run_status=base.RunStatus(),
                                                      start_time=start_time))
        except FileNotFoundError as e:
            # The other executors recognize inaccessible working directories or missing commands
            # only after the wait_for(). We emulate this behaviour here such that all executors
            # behave identically with respect to these problems.
            if e.strerror == f"No such file or directory: {command.workdir.__repr__()}":
                # cd /dir/does/not/exist: exit code 1
                exit_code = 1
            else:
                # Command not executable: exit code 127
                exit_code = 127

            return base.ExecutedProcess(executor=self,
                                        process_handle=None,
                                        pre_result=base.
                                        CommandResult(command=command,
                                                      id=base.ProcessId(None),
                                                      stdout_file=stdout_file,
                                                      stderr_file=stderr_file,
                                                      stdin_file=stdin_file,
                                                      run_status=base.RunStatus(
                                                          exit_code, message=e.strerror),
                                                      start_time=start_time))

    def copy_file(self, source: PathLike, target: PathLike):
        if Path(source) == Path(target):
            raise ValueError("Identical source and target paths: '{source}'")
        else:
            copyfile(source, target)

    def remove_file(self, target: PathLike):
        os.unlink(target)

    def get_status(self, process: base.ExecutedProcess) -> base.RunStatus:
        if process.handle is None:
            return process.result.status
        else:
            return base.RunStatus(process.handle.poll())

    def update_process(self, process: base.ExecutedProcess) -> base.ExecutedProcess:
        """
        Update the executed process, if possible.
        """
        if process.handle is None:
            # There is no process handle. We cannot update the result.
            return process
        else:
            result = process.result
            return_code = process.handle.poll()
            if return_code is not None:
                result.status = base.RunStatus(return_code)
                result.end_time = datetime.now()
                process.result = result
            return process

    def kill(self, process: base.ExecutedProcess):
        if process.handle is not None:
            process.handle.terminate()
        # TODO The API says little. The code says it uses os.kill for Unix. More recherche needed.

    def wait_for(self, process: base.ExecutedProcess, timeout: Optional[float] = None)\
            -> base.CommandResult:
        status = self.get_status(process)
        if not status.finished:
            logger.debug(f"Waiting for process {process.id}")
            process.handle.wait(timeout)
        return self.update_process(process).result
