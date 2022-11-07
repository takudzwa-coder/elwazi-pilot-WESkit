#  Copyright (c) 2022. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
import json
import logging
from datetime import timedelta, datetime
from functools import singledispatch
from importlib import import_module
from json import JSONEncoder
from pathlib import PosixPath
from typing import Callable, Optional, Dict
from uuid import UUID

from kombu.serialization import register
from urllib3.util import Url, parse_url

from weskit.memory_units import Memory
from weskit.utils import identity

logger = logging.getLogger(__name__)


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
          implementer is freed of this load. Instead, typed deserialization is modeled by
          added __type__ tags in the DispatchingEncode and the from_json() decoder function.
    """
    if hasattr(obj, "encode_json"):
        return obj.encode_json()
    else:
        return obj


class DispatchingEncoder(JSONEncoder):
    """
    A JSONEncoder that can be used with `json.dumps(obj, cls=DispatchingEncoder)` and that makes
    use af the single-dispatch encode_json() mechanism.

    This should work with all types that have an encode_json() single-dispatch method defined or --
    because of its default implementation -- with all classes defining an encode_json() instance
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


class DecoderRegistry:
    """
    Create a registry for a value-dispatch function.

    If a value matches the apply_p predicate it is considered valid input to the decoder.
    If you try to decode a value with this decoder that is not valid input it will simply return
    the un-decoded value.

    A valid value can be translated into a key by a key-function `get_key` and into a decoded
    value by a `get_data` function, if a decoder is registered for the key.

    The registry is a decorator. So you can create the registry

       decode_json = DecoderRegistry(...)

    and then register new decoder for with

    @decoder_json.register(value)
    def _(obj):
       ...

    This will register a decoder for the value `value`. Later for decoding you can do

    decode_json(raw_value)

    The get_key and get_data functions in the registry map the raw value to the key that is
    used to search the registry index to find a decoder function that was previously registered with
    the register function. The decoder is called with the result of the get_data function.

    If you want to handle key-misses, i.e. unregistered value properties (e.g. some value for
    a "__type__" field that you didn't register, you can define a default decoder. By default,
    the default_decoder just returns the value as decoded value, but you may also e.g. raise
    an exception.

    Note that the default decode has a different signature. It gets the both the key and the data
    because the key may contain information about how to decode the data, e.g. a type name.
    """

    def __init__(self,
                 apply_p: Callable[[object], bool],
                 get_key: Optional[Callable] = identity,
                 get_data: Optional[Callable] = identity,
                 default_decoder: Optional[Callable] = lambda key, obj: obj):
        self._decoders: Dict = {}
        self._default_decoder = default_decoder
        self._apply_p = apply_p
        self._get_key = get_key
        self._get_data = get_data

    @property
    def registry(self):
        return dict(**self._decoders)

    def register(self, key):

        def wrapper(decoder):
            self._decoders[key] = decoder

            def decorated_decoder():
                return decoder
            return decorated_decoder
        return wrapper

    def __call__(self, raw_value):
        if self._apply_p(raw_value):
            key = self._get_key(raw_value)
            if key in self._decoders:
                return self._decoders[key](self._get_data(raw_value))
            else:
                return self._default_decoder(key, self._get_data(raw_value))
        else:
            return raw_value


def default_decoder(fqcn, data):
    """
    By default, the target is an instance of the class designated by fqcn and that the class has a
    decode_json method.
    Thus, for classes you can either register a decoder function with the decorator, or simply
    add a decode_json method.
    """
    fqcn_segments = fqcn.split(".")
    modnames = fqcn_segments[0:-1]
    classname = fqcn_segments[-1]
    module = import_module(".".join(modnames))
    cls = getattr(module, classname)
    if hasattr(cls, "decode_json"):
        return cls.decode_json(data)
    else:
        # If fqcn is not the fully qualified name of a class that has a decode_json
        # method, throw an exception.
        raise RuntimeError(f"JSON has __type__ and __data__ fields but '{cls}'"
                           " has no decode_json() class method")


# A decoder registry for `{"__type__": key, "__data__": data}` values. If the key and data map
# functions are presented with values of other types, e.g. `str`, they will probably fail.
# A decoder key that is not registered is handled by the default decoder, which is `identity(x)`.
decode_json = DecoderRegistry(
    apply_p=lambda obj: isinstance(obj, dict) and "__type__" in obj and "__data__" in obj,
    get_key=lambda x: x["__type__"],
    get_data=lambda x: x["__data__"],
    default_decoder=default_decoder)


def from_json(obj: str):
    """
    Like to_json(), but for deserialization. This uses the __type__ and __data__ fields in the
    JSON to identify the class/type of an object and searches the class for a from_json() class
    method.

    JSON without __type__ or __data__ fields is deserialized simply with json.loads(obj).
    """
    return json.loads(obj, object_hook=decode_json)


@encode_json.register(timedelta)
def _(obj: timedelta):            # Note: dispatch variants are anonymous (_)
    """
    Allow serialization of datetime.timedelta via this single-dispatch function.

    timedelta.total_seconds returns the interval length -- including microseconds -- as float.
    """
    return str(obj.total_seconds())


@decode_json.register("datetime.timedelta")
def _(value):
    return timedelta(seconds=float(value))


@encode_json.register(datetime)
def _(obj: datetime):
    return obj.isoformat()


@decode_json.register("datetime.datetime")
def _(obj) -> datetime:
    return datetime.fromisoformat(obj)


@encode_json.register(Memory)
def _(obj: Memory):
    return str(obj)


@decode_json.register("weskit.memory_units.Memory")
def _(value):
    return Memory.from_str(value)


@encode_json.register(PosixPath)
def _(obj: PosixPath):
    return str(obj)


@decode_json.register("pathlib.PosixPath")
def _(obj) -> PosixPath:
    return PosixPath(obj)


@encode_json.register(UUID)
def _(obj) -> str:
    return str(obj)


@decode_json.register("uuid.UUID")
def _(value):
    return UUID(value)


@encode_json.register(Url)
def _(obj) -> str:
    return str(obj)


@decode_json.register("urllib3.util.Url")
def _(value):
    return parse_url(value)


# Register DispatchingEncoder via to_json() and corresponding from_json() with kombu (used by
# Celery).
register("WESkitJSON",
         encoder=to_json,
         decoder=from_json,
         content_type='application/x-WESkitJSON',
         content_encoding='utf-8')
