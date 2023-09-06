# Copyright (c) 2022. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
# SPDX-FileCopyrightText: 2023 2023 The WESkit Team
#
# SPDX-License-Identifier: MIT

# If True, the task will report their status as ‘started’ when the task is executed by a worker.
task_track_started = True

# Set the result expiration time to 30 days (default = 86400 sec = 1 d)
result_expires = 2592000

# Serialization
serializer = "WESkitJSON"
task_serializer = "WESkitJSON"
result_serializer = "WESkitJSON"
accept_content = ["application/x-WESkitJSON"]
