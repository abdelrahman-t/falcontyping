"""
The MIT License (MIT)

Copyright (c) 2018 Tomoya Kose

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

This is a modified version of the decoding module at:
https://github.com/mitsuse/typedjson-python/blob/master/typedjson/decoding.py

Author: Tomoya Kose <tomoya@mitsuse.jp>
Repository: https://github.com/mitsuse/typedjson-python
"""
from typing import Any, Type, TypeVar, Union

from .base import (Decoded, DecodingError, ExternalSerializerException, Path,
                   TypeMismatch, UnsupportedDecoding)

try:
    from pydantic import BaseModel as PydanticBaseModel

except ImportError:
    PydanticBaseModel = None  # type: ignore


try:
    from marshmallow import Schema as MarshmallowSchema

except ImportError:
    MarshmallowSchema = None  # type: ignore

_PRIMITIVE_TYPES = (str, float, int, bool, type(None))


def parse_int_from_string(json: str, path: Path) -> Union[Decoded, DecodingError]:
    try:
        number = float(json)

        if not number.is_integer():
            raise ValueError

        return int(number)  # type: ignore

    except ValueError:
        return DecodingError(TypeMismatch(path))


def parse_pydantic_from_dict(type_: Any, json: Any, path: Path) -> Union[Decoded, DecodingError]:
    try:
        return type_(**json)  # type: ignore

    except Exception as e:
        return DecodingError(reason=ExternalSerializerException(path, exception=e))


def parse_marshmallow_from_dict(type_: Any, json: Any, path: Path) -> Union[Decoded, DecodingError]:
    try:
        return type_().load(json)  # type: ignore

    except Exception as e:
        return DecodingError(reason=ExternalSerializerException(path, exception=e))


def decode(type_: Type[Decoded], json: Any, path: Path = ()) -> Union[Decoded, DecodingError]:
    decoders = (
        decode_as_union,
        decode_as_primitive,
        decode_as_model
    )

    result_final: Union[Decoded, DecodingError] = DecodingError(
        UnsupportedDecoding(path)
    )
    for decoder in decoders:
        result = decoder(type_, json, path)

        if isinstance(result, DecodingError):
            if isinstance(result.reason, TypeMismatch):
                result_final = result
        else:
            result_final = result
            break

    return result_final


def decode_as_model(type_: Type[Decoded], json: Any, path: Path) -> Union[Decoded, DecodingError]:
    from .annotation import origin_of

    if origin_of(type_) in (Union, Any, ):
        return DecodingError(UnsupportedDecoding(path))

    if isinstance(json, type_):
        return json

    if PydanticBaseModel and issubclass(type_, PydanticBaseModel):
        if json:
            return parse_pydantic_from_dict(type_, json=json, path=path)

        else:
            return DecodingError(TypeMismatch(path))

    elif MarshmallowSchema and issubclass(type_, MarshmallowSchema):
        if json:
            return parse_marshmallow_from_dict(type_, json=json, path=path)

        else:
            return DecodingError(TypeMismatch(path))

    else:
        return DecodingError(UnsupportedDecoding(path))


def decode_as_primitive(type_: Type[Decoded], json: Any, path: Path) -> Union[Decoded, DecodingError]:
    if type_ not in _PRIMITIVE_TYPES:
        return DecodingError(UnsupportedDecoding(path))

    if isinstance(json, type_):
        return json

    if type_ is int and isinstance(json, str):
        return parse_int_from_string(json, path)

    else:
        return DecodingError(TypeMismatch(path))


def decode_as_union(type_: Type[Decoded], json: Any, path: Path) -> Union[Decoded, DecodingError]:
    from .annotation import args_of
    from .annotation import origin_of

    if origin_of(type_) is Union:
        args = args_of(type_)

        for type_ in args:
            if type_.__class__ is TypeVar:
                return DecodingError(UnsupportedDecoding(path))

        for type_ in args:
            decoded = decode(type_, json, path)

            if not isinstance(decoded, DecodingError):
                break

        return decoded
    else:
        return DecodingError(UnsupportedDecoding(path))
