# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

from typing import Dict, Union, Any

from weskit.classes.WorkflowEngine import WorkflowEngine, ActualWorkflowEngine, \
                                          SingularityWrappedEngine
from weskit.classes.EngineExecutorType import EngineExecutorType
from weskit.classes.PathContext import PathContext

# Type aliases to simplify the signature of the type annotations.
ConfigParams = Dict[str, Dict[str, Any]]


class WorkflowFactory:
    """
    Wrappes a workflow engine command when workload is executed remotely.
    """
    @staticmethod
    def create_wrapper(config_file: ConfigParams,
                       executor_context: PathContext,
                       workflow_engine: ActualWorkflowEngine) \
            -> Union[WorkflowEngine, ActualWorkflowEngine]:

        executor_type = EngineExecutorType.from_string(str(config_file["executor"]["type"]))
        if executor_type.needs_login_credentials:
            return SingularityWrappedEngine(workflow_engine, executor_context)
        else:
            return workflow_engine
