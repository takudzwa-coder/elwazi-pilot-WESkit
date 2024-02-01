# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

from pathlib import Path
import pytest
import os
import json
from urllib3.util.url import parse_url
from weskit.classes.ShellCommand import ShellCommand, ss
from weskit.classes.executor2.CommandWrapper import CommandWrapper
from weskit.classes.executor2.ProcessId import WESkitExecutionId

EXECUTION_ID = WESkitExecutionId()
CURRENT_DIR = Path(os.path.curdir).absolute().as_posix()


def append_optional_values_to_command(command_output, parameter, file_name, result):
    file_name = command_output.get(file_name)
    if file_name is not None:
        result.command.append(parameter)
        result.command.append(f"{file_name}")


def load_input_data(testcase):
    return json.load(open("tests/executor2/command-data/input.json")).get(testcase)


def load_output_data(testcase):
    return json.load(open("tests/executor2/command-data/output.json")).get(testcase)


def parse_optional_file(file_name):
    if file_name is not None:
        file_name = parse_url(file_name)
    return file_name


def populate_wrapped_command_from_output_file(command_output):
    command = ShellCommand(command=command_output["command"])
    result = ShellCommand(
        command=[
            f"{CURRENT_DIR}/{command_output.get('wrapperDir')}/wrap",
            "-a", "-w", f"{CURRENT_DIR}", "-l",
            f"{CURRENT_DIR}/{command_output.get('logDir')}/{EXECUTION_ID.value}",
        ],
        workdir=Path(command_output["workDir"])
    )
    append_optional_values_to_command(command_output, "-n", "envFile", result)
    append_optional_values_to_command(command_output, "-o", "stdoutFile", result)
    append_optional_values_to_command(command_output, "-e", "stderrFile", result)
    append_optional_values_to_command(command_output, "-i", "stdinFile", result)
    result.command.append("--")
    result.command.append(command.command_expression)
    result.command.append(ss("1>"))
    result.command.append(
        f"{CURRENT_DIR}/{command_output.get('logDir')}/{EXECUTION_ID.value}/wrapper_stdout"
        )
    result.command.append(ss("2>"))
    result.command.append(
        f"{CURRENT_DIR}/{command_output.get('logDir')}/{EXECUTION_ID.value}/wrapper_stderr"
        )
    return result


@pytest.mark.parametrize(
    "command_data, command_output",
    [
        (
            load_input_data("eval_success_stdout_stderr_env"),
            load_output_data("eval_success_stdout_stderr_env"),
        ),
        (
            load_input_data("eval_success_stdout_stderr"),
            load_output_data("eval_success_stdout_stderr"),
        ),
        (
            load_input_data("eval_success"),
            load_output_data("eval_success"),
        )
    ],
)
def test_generate_wrapped_command(command_data, command_output):
    input_command = command_data.get("command")
    workdir = command_data.get("workDir")
    wrapper_dir = command_data.get("wrapperDir")
    log_dir_base = command_data.get("logDir")
    env_file = command_data.get("envFile")
    stdout_url = command_data.get("stdoutFile")
    stderr_url = command_data.get("stderrFile")
    stdin_url = command_data.get("stdinFile")
    wrapped_command = populate_wrapped_command_from_output_file(command_output)

    command = ShellCommand(
        command=input_command,
        workdir=Path(workdir),
    )

    wrapper_command = CommandWrapper(
        execution_id=EXECUTION_ID,
        command=command,
        wrapper_dir=Path(wrapper_dir),
        log_dir_base=log_dir_base,
        as_background_process=False,
        env_file=parse_optional_file(env_file),
        stdout_url=parse_optional_file(stdout_url),
        stderr_url=parse_optional_file(stderr_url),
        stdin_url=parse_optional_file(stdin_url),
    )
    generated_command = wrapper_command.generate_wrapped_command()
    assert wrapped_command.command == generated_command.command


@pytest.mark.parametrize(
    "command_data, command_output",
    [
        (
            load_input_data("no_work_dir"),
            load_output_data("no_work_dir"),
        )
    ],
)
def test_empty_work_dir(command_data, command_output):
    input_command = command_data.get("command")
    wrapper_dir = command_data.get("wrapperDir")
    log_dir_base = command_data.get("logDir")
    stdout_url = command_data.get("stdoutFile")
    stderr_url = command_data.get("stderrFile")
    stdin_url = command_data.get("stdinFile")

    command = ShellCommand(command=input_command)
    wrapper_command = CommandWrapper(
        execution_id=EXECUTION_ID,
        command=command,
        wrapper_dir=Path(wrapper_dir),
        log_dir_base=log_dir_base,
        as_background_process=False,
        stdout_url=parse_url(url=stdout_url),
        stderr_url=parse_url(url=stderr_url),
        stdin_url=parse_url(url=stdin_url),
    )
    with pytest.raises(ValueError) as error:
        _ = wrapper_command.generate_wrapped_command()
    assert str(error.value) == command_output["error"]


@pytest.mark.parametrize(
    "command_data, command_output",
    [
        (
            load_input_data("incorrect_stderr_schema"),
            load_output_data("incorrect_url_schema"),
        ),
        (
            load_input_data("incorrect_stdout_schema"),
            load_output_data("incorrect_url_schema"),
        ),
        (
            load_input_data("incorrect_stdin_schema"),
            load_output_data("incorrect_url_schema"),
        ),
    ],
)
def test_incorrect_url_schema(command_data, command_output):
    input_command = command_data.get("command")
    workdir = command_data.get("workDir")
    wrapper_dir = command_data.get("wrapperDir")
    log_dir_base = command_data.get("logDir")
    stdout_url = command_data.get("stdoutFile")
    stderr_url = command_data.get("stderrFile")
    stdin_url = command_data.get("stdinFile")

    command = ShellCommand(
        command=input_command,
        workdir=Path(workdir),
    )
    wrapper_command = CommandWrapper(
        execution_id=EXECUTION_ID,
        command=command,
        wrapper_dir=Path(wrapper_dir),
        log_dir_base=log_dir_base,
        as_background_process=False,
        stdout_url=parse_url(url=stdout_url),
        stderr_url=parse_url(url=stderr_url),
        stdin_url=parse_url(url=stdin_url),
    )
    with pytest.raises(ValueError) as error:
        _ = wrapper_command.generate_wrapped_command()
    assert str(error.value) == command_output.get("error")
