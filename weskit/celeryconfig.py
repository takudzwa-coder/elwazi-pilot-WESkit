#  Copyright (c) 2022. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
#
# Put the static Celery configuration options here.

# If True, the task will report their status as ‘started’ when the task is executed by a worker.
task_track_started = True

# Set the result expiration time to 7 days (default = 86400 sec = 1 d)
result_expires = 604800

# Serialization
serializer = "WESkitJSON"
task_serializer = "WESkitJSON"
result_serializer = "WESkitJSON"
accept_content = ["application/x-WESkitJSON"]
