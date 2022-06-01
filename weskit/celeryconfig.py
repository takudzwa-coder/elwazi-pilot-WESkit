#  Copyright (c) 2022. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
#
# Put the static Celery configuration options here.

serializer = "WESkitJSON"
task_serializer = "WESkitJSON"
result_serializer = "WESkitJSON"
accept_content = ["application/x-WESkitJSON"]
