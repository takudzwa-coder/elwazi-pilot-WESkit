# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

from typing import Dict, List, Union, Optional

from weskit.classes.PathContext import PathContext
from weskit.classes.WorkflowEngine import Snakemake, Nextflow,\
    ActualWorkflowEngine, SingularityWrappedEngine, WorkflowEngine
from weskit.classes.WorkflowEngineParameters import ActualEngineParameter

# Type aliases to simplify the signature of the type annotations.
ConfParameter = Dict[str, Optional[Union[str, bool]]]
ConfParameters = List[ConfParameter]
ConfVersions = Dict[str, ConfParameters]


class WorkflowEngineFactory:
    """
    Create a data index structure from an engine specification as found in the `weskit.yaml`.
    The index has the shape $engineName:str -> $version:str -> WorkflowEngine. The
    WorkflowEngine is pre-configured with the default workflow engine parameters taken from the
    `weskit.yaml`.
    """

    @staticmethod
    def create_engine(engine_class,
                      engine_version: str,
                      parameters: ConfParameters) \
            -> ActualWorkflowEngine:
        """
        Convert a list of parameter name/value dictionaries of actual parameters to a dictionary of
        ActualEngineParams.

        Raises a KeyError, if the parameter name is not among the aliases of all allowed parameters
        for this WorkflowEngine.
        """
        actual_params = []
        for p in parameters:
            param = engine_class.known_parameters()[p["name"]]
            value = p.get("value", None)
            is_api_parameter = bool(p.get("api", False))   # type was checked by validation
            actual_params += [ActualEngineParameter(param,
                                                    None if value is None else str(value),
                                                    is_api_parameter)]
        return engine_class(engine_version,
                            actual_params)

    @staticmethod
    def _create_versions(engine_class,
                         engine_params: Dict[str, Union[ConfVersions]],
                         execution_path_context: PathContext) \
            -> Dict[str, Union[ActualWorkflowEngine, WorkflowEngine]]:
        """
        :param engine_class: WorkflowEngine class
        :param engine_params: Version name -> List of dictionaries, one for each parameter.
        :return:
        """
        return dict(map(lambda by_version: (by_version[0],
                                            WorkflowEngineFactory.
                                            create_engine(engine_class,
                                                          by_version[0],
                                                          by_version[1]['default_parameters'])
                                            if "singularity" not in by_version[0]
                                            else
                                            SingularityWrappedEngine(
                                                    WorkflowEngineFactory.
                                                    create_engine(engine_class,
                                                                  by_version[0],
                                                                  by_version[1]
                                                                  ['default_parameters']),
                                                    execution_path_context
                                            )),
                        engine_params.items()))

    @staticmethod
    def _maybe_engine(engine_class,
                      engine_params: Dict[str, Dict[str, ConfVersions]],
                      execution_path_context: PathContext) \
            -> Dict[str, Dict[str, Union[ActualWorkflowEngine, WorkflowEngine]]]:
        """
        Create a WorkflowEngine entry, if the engine is defined in the configuration.
        """
        def engine_is_defined() -> bool:
            return engine_class.name() in engine_params

        def some_version_is_defined() -> bool:
            return len(engine_params[engine_class.name()]) > 0

        if engine_is_defined() and some_version_is_defined():
            return {engine_class.name(): WorkflowEngineFactory.
                    _create_versions(engine_class,
                                     {version: configuration_option
                                      for version, configuration_option
                                      in engine_params[engine_class.name()].items()
                                      },
                                     execution_path_context)}
        else:
            return {}

    @staticmethod
    def create(engine_params: Dict[str, Dict[str, ConfVersions]],
               execution_path_context: PathContext) -> \
            Dict[str, Dict[str, Union[ActualWorkflowEngine, WorkflowEngine]]]:
        """
        Return a dictionary of all WorkflowEngines mapping workflow_engine to
        workflow_engine_version to WorkflowEngine instances.

        The `execution_path_context` is needed if the actual workflow engine (e.g. Snakemake)
        has to be wrapped by a container. The container needs to know which external paths to
        mount into the container.

        This is yet statically implemented, but could at some
        point by done with https://stackoverflow.com/a/3862957/8784544.
        """
        workflow_engines = {}
        workflow_engines.update(WorkflowEngineFactory._maybe_engine(Snakemake,
                                                                    engine_params,
                                                                    execution_path_context))
        workflow_engines.update(WorkflowEngineFactory._maybe_engine(Nextflow,
                                                                    engine_params,
                                                                    execution_path_context))

        # The semantics of workflow_type and workflow_engine_parameters is not completely defined
        # yet. There is also a proposal for a workflow_engine_name parameter.
        # Compare https://gitlab.com/one-touch-pipeline/weskit/api/-/issues/91
        # See also https://github.com/ga4gh/workflow-execution-service-schemas/issues/171

        return workflow_engines
