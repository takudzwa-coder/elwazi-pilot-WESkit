# Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
# SPDX-FileCopyrightText: 2023 2023 The WESkit Team
#
# SPDX-License-Identifier: MIT

import enum


class ErrorCodes(enum.Enum):
    SUCCESS = 0
    CONFIGURATION_ERROR = 1
    LOGIN_CONFIGURATION_ERROR = 2
