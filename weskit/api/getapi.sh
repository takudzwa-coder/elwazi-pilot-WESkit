# Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
# SPDX-FileCopyrightText: 2023 2023 The WESkit Team
#
# SPDX-License-Identifier: MIT

APIURL="https://raw.githubusercontent.com/ga4gh/workflow-execution-service-schemas/master/openapi/workflow_execution_service.swagger.yaml"
APIOUT="20191217_workflow_execution_service.swagger.yaml"
wget $APIURL -O $APIOUT