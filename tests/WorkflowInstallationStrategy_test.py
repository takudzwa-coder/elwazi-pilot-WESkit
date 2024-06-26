# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

from pathlib import Path

from weskit.classes.TrsWorkflowInstaller import WorkflowInfo


def test_parse_trs_uri():
    info = WorkflowInfo.from_uri_string("trs://server/workflow/version/SMK/primary")
    assert info.name == "workflow"
    assert info.version == "version"
    assert info.type == "SMK"
    assert info.workflow_engine_id == "SMK"
    assert info.primary_file == Path("primary")

    info = WorkflowInfo.from_uri_string("trs://server:1234/workflow/version/PLAIN_SMK/primary")
    assert info.type == "PLAIN_SMK"
    assert info.workflow_engine_id == "SMK"

    info = WorkflowInfo.from_uri_string("trs://server/workflow/version/NFL/primary")
    assert info.type == "NFL"
    assert info.workflow_engine_id == "NFL"

    info = WorkflowInfo.from_uri_string("trs://server/workflow/version/PLAIN_NFL/primary")
    assert info.type == "PLAIN_NFL"
    assert info.workflow_engine_id == "NFL"

    info = WorkflowInfo.from_uri_string("trs://server/workflow/version/PLAIN_SMK/Snakefile")
    assert info.primary_file == Path("Snakefile")
