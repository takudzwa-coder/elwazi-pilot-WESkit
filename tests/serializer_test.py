# SPDX-FileCopyrightText: 2023 The WESkit Team
#
# SPDX-License-Identifier: MIT

from datetime import timedelta

from weskit.memory_units import Unit, Memory
from weskit.serializer import DispatchingEncoder, to_json, from_json


def test_generic_encoder_timedelta():
    encoder = DispatchingEncoder()
    json = {
        "delta": timedelta(hours=1)
    }
    assert encoder.encode(json) == \
           '{"delta": {"__type__": "datetime.timedelta", "__data__": "3600.0"}}'


def test_generic_encoder_memory():
    encoder = DispatchingEncoder()
    json = {
        "mem": Memory(1, Unit.MEGA)
    }
    assert encoder.encode(json) == \
           '{"mem": {"__type__": "weskit.memory_units.Memory", "__data__": "1MB"}}'


def test_to_json():
    json = '{"mem": {"__type__": "weskit.memory_units.Memory", "__data__": "1MB"},' + \
           ' "delta": {"__type__": "datetime.timedelta", "__data__": "3600.0"}}'
    obj = {
        "mem": Memory(1, Unit.MEGA),
        "delta": timedelta(hours=1)
    }
    assert to_json(obj) == json


def test_from_json():
    json = '{"mem": {"__type__": "weskit.memory_units.Memory", "__data__": "1MB"},' + \
           ' "delta": {"__type__": "datetime.timedelta", "__data__": "3600.0"}}'
    obj = {
        "mem": Memory(1, Unit.MEGA),
        "delta": timedelta(hours=1)
    }
    assert from_json(json) == obj
