# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

from typing import Dict, Union, Optional

from weskit.classes.WorkflowEngine import WorkflowEngine, SingularityWrappedEngine
from weskit.classes.EngineExecutorType import EngineExecutorType
from weskit.classes.PathContext import PathContext

# Type aliases to simplify the signature of the type annotations.
RetryParameters = Dict[str, Union[Dict[str, int], int]]
LoginParameters = Dict[str, Union[str, int, Optional[RetryParameters]]]


class WorkflowFactory:
    """
    fdsfds
    """

    @staticmethod
    def _wrap_workflow(login_params: LoginParameters,
                       workflow_engine: WorkflowEngine,
                       executor_context: PathContext) -> WorkflowEngine:
        """
        """
        executor_type = EngineExecutorType.from_string(str(login_params["type"]))
        if executor_type.needs_login_credentials:
            return SingularityWrappedEngine(workflow_engine, executor_context)
        else:
            return workflow_engine

    @staticmethod
    def create(config_file: Dict, executor_context: PathContext,
               workflow_engine: WorkflowEngine) -> WorkflowEngine:
        """
        dfsafds
        """
        workflow_wrapper = WorkflowFactory._wrap_workflow(config_file["executor"],
                                                          workflow_engine,
                                                          executor_context)

        return workflow_wrapper
