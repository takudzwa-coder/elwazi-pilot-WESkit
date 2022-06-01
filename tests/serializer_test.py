#  Copyright (c) 2022. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

from datetime import timedelta

from weskit.memory_units import Unit, Memory
from weskit.serializer import DispatchingEncoder


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
