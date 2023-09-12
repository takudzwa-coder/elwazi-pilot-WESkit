# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

APIURL="https://raw.githubusercontent.com/ga4gh/workflow-execution-service-schemas/master/openapi/workflow_execution_service.swagger.yaml"
APIOUT="20191217_workflow_execution_service.swagger.yaml"
wget $APIURL -O $APIOUT