# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

from urllib3.util.url import Url
from typing import List, Optional, Union, cast
from pathlib import Path
from weskit.classes.ShellCommand import ShellCommand, ShellSpecial, ss
from weskit.classes.executor2.ProcessId import WESkitExecutionId

from weskit.utils import resource_path


class CommandWrapper:
    """
    Return a ShellCommand derived from the input command that allows the command to be run
    in the background and includes logging to the requested output files and of the
    exit code.

    The execution logs go into a directory `.log-{execution_id}`, unless other files
    were requested via the `stdout_url`, etc. parameters.

    Note that the stdout and stderr of the wrapper script is written to the log_dir/wrapper_stdout
    and log_dir/wrapper_stderr files.

    The -n parameter of the wrapper, attaches environment variables to the wrapped command.
    """

    def __init__(
        self,
        execution_id: WESkitExecutionId,
        command: ShellCommand,
        wrapper_dir: Path,
        log_dir_base: Path,
        as_background_process: bool,
        env_file: Optional[Url] = None,
        stdout_url: Optional[Url] = None,
        stderr_url: Optional[Url] = None,
        stdin_url: Optional[Url] = None,
    ):
        self._execution_id = execution_id
        self._command = command
        self._wrapper_dir = wrapper_dir
        self._log_dir_base = log_dir_base
        self._as_background_process = as_background_process
        self._env_file = env_file
        self._stdout_url = stdout_url
        self._stderr_url = stderr_url
        self._stdin_url = stdin_url

    @property
    def execution_id(self) -> WESkitExecutionId:
        return self._execution_id

    @property
    def command(self) -> ShellCommand:
        return self._command

    @property
    def wrapper_dir(self) -> Path:
        return self._wrapper_dir

    @property
    def log_dir_base(self) -> Path:
        return self._log_dir_base

    @property
    def as_background_process(self) -> bool:
        return self._as_background_process

    @property
    def env_file(self) -> Optional[Url]:
        return self._env_file

    @property
    def stdout_url(self) -> Optional[Url]:
        return self._stdout_url

    @property
    def stderr_url(self) -> Optional[Url]:
        return self._stderr_url

    @property
    def stdin_url(self) -> Optional[Url]:
        return self._stdin_url

    def _file_url_to_path(self, url: Url) -> Path:
        if url.scheme is None:
            raise ValueError(
                "Executor only accepts file:// URLs for stdin/stdout/stderr."
            )
        elif url.scheme is not None and url.scheme != "file":
            raise ValueError(
                "Executor only accepts file:// URLs for stdin/stdout/stderr."
            )
        elif url.path is None:
            raise ValueError("Path not set for stdin/stdout/stderr.")
        return Path(url.path)

    @property
    def _wrapper_source_path(self) -> Path:
        return cast(Path, resource_path("weskit.classes.executor2.resources", "wrap"))

    def _command_log_dir(self) -> Path:
        """
        Return the logging directory for the process.
        """
        if self._command.workdir is None:
            raise ValueError("Work directory has not been set.")
        return (
            self._command.workdir / self._log_dir_base / str(self._execution_id.value)
        )

    def generate_wrapped_command(self) -> ShellCommand:
        if self.command.workdir is None:
            raise ValueError(
                "No workdir for command. Currently only support commands with defined workdir."
            )

        def _optional_file(param: str, url: Optional[Url]) -> List[str]:
            optional_file = []
            if url is not None:
                path = self._file_url_to_path(url)
                optional_file.append(param)
                optional_file.append(path.absolute().as_posix())
            return optional_file

        command_log_dir = self._command_log_dir()
        wrapped_command: List[Union[str, ShellSpecial]] = list()
        # Ensure process is not killed upon shell exit.
        if self.as_background_process:
            wrapped_command += ["nohup"]
        wrapped_command += [self.wrapper_dir.joinpath("wrap").absolute().as_posix(), "-a"]
        # A working directory is mandatory!
        wrapped_command += ["-w", self.command.workdir.absolute().as_posix()]
        wrapped_command += ["-l", command_log_dir.absolute().as_posix()]
        wrapped_command += _optional_file("-n", self.env_file)
        wrapped_command += _optional_file("-o", self.stdout_url)
        wrapped_command += _optional_file("-e", self.stderr_url)
        wrapped_command += _optional_file("-i", self.stdin_url)
        wrapped_command += ["--", self.command.command_expression]
        wrapped_command += [
            ss("1>"),
            command_log_dir.joinpath("wrapper_stdout").absolute().as_posix()
        ]
        wrapped_command += [
            ss("2>"),
            command_log_dir.joinpath("wrapper_stderr").absolute().as_posix()
        ]
        if self.as_background_process:
            wrapped_command += [ss("&")]
        return self.command.copy(command=wrapped_command)
