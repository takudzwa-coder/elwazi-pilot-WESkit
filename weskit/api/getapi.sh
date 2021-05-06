#
# Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
# Distributed under the MIT License. Full text at
#
#     https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
# Authors: The WESkit Team
#

APIURL="https://raw.githubusercontent.com/ga4gh/workflow-execution-service-schemas/master/openapi/workflow_execution_service.swagger.yaml"
APIOUT="20191217_workflow_execution_service.swagger.yaml"
wget $APIURL -O $APIOUT