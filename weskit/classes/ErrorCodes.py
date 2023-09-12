# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

import enum


class ErrorCodes(enum.Enum):
    SUCCESS = 0
    CONFIGURATION_ERROR = 1
    LOGIN_CONFIGURATION_ERROR = 2
