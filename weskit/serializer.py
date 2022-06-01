#  Copyright (c) 2022. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
import json
from datetime import timedelta
from functools import singledispatch
from json import JSONEncoder

from kombu.serialization import register

from weskit.memory_units import Memory


@singledispatch
def encode_json(obj):
    """
    Let's use singledispatch of functions to model something more generic that allows us to
    easily define typed from/to JSON conversion methods or functions for existing types or new ones.

    This is the default encode_json() dispatch method that will be called only, if no type-specific
    method is registered.

    If the object has a method called `encode_json`, then it is used. Otherwise, return the object
    as is, which boils down to using the default JSON conversion used by the JSONEncoder (in
    DispatchingEncoder).

    The output is assumed to be fed to json.dumps(). Therefore, if you want to make an
    object serializable, you either define an encode_json() method on the class or attach an
    encode_json() single-dispatch function to the type.

    See below for an implementation with datetime.timedelta and Memory.

    NOTE: The type-tags are not returned by the encode_json functions. The idea is that the
          implementer is freed of this load. Instead typed deserialization is modeled by
          added __type__ tags in the DispatchingEncode and the from_json() decoder function.
    """
    if hasattr(obj, "encode_json"):
        return obj.encode_json()
    else:
        return obj


@encode_json.register(timedelta)
def _(obj: timedelta):            # Note: dispatch variants are anonymous (_)
    """
    Allow serialization of datetime.timedelta via this single-dispatch function.

    timedelta.total_seconds returns the interval length -- including microseconds -- as float.
    """
    return str(obj.total_seconds())


@encode_json.register(Memory)
def _(obj: Memory):
    return str(obj)


class DispatchingEncoder(JSONEncoder):
    """
    A JSONEncoder that can be used with `json.dumps(obj, cls=DispatchingEncoder)` and that makes
    use af the single-dispatch encode_json() mechanism.

    This should work with all types that have a encode_json() single-dispatch method defined or --
    because of its default implementation -- with all classes defining a encode_json() instance
    method.

    Note that this encoder wraps all results from encode_json (method or single-dispatch method)
    into a dictionary with __type__ and __data__ fields.
    """
    def default(self, obj):
        new_obj = encode_json(obj)
        if new_obj is not obj:
            # Use the fully qualified class name as type tag.
            fqcn = obj.__class__.__module__ + "." + obj.__class__.__qualname__
            return {
                "__type__": fqcn,
                "__data__": new_obj
            }
        else:
            return super(DispatchingEncoder, self).default(obj)


def to_json(obj) -> str:
    """
    Produce a JSON string from an object using the DispatchingEncoder that uses the singledispatch
    functions encode_json().
    """
    return json.dumps(obj, cls=DispatchingEncoder)


def from_json(obj):
    """
    Like to_json(), but for deserialization. This uses the __type__ and __data__ fields in the
    JSON to identify the class/type of an object and searches the class for a from_json() class
    method.

    JSON without __type__ or __data__ fields is deserialized simply with json.loads(obj).
    """
    if type(obj) == "dict" and "__type__" in obj and "__data__" in obj:
        cls = globals()[obj['__type__']]
        if hasattr(cls, "from_json"):
            return cls.from_json(obj["__data__"])
        else:
            raise RuntimeError(f"JSON has __type__ and __data__ fields but '{cls}'"
                               " has no from_json() class method")
    else:
        return json.loads(obj)


# Register DispatchingEncoder via to_json() and corresponding from_json() with kombu (used by
# Celery).
register("WESkitJSON",
         encoder=to_json,
         decoder=from_json,
         content_type='application/x-WESkitJSON',
         content_encoding='utf-8')
