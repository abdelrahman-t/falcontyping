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
from typing import Any, Tuple, TypeVar, Union

Decoded = TypeVar('Decoded')
Value = TypeVar('Value')

Path = Tuple[str, ...]


class TypeMismatch(Exception):
    def __init__(self, path: Path) -> None:
        self.__path = path

    def __eq__(self, x: Any) -> bool:
        if isinstance(x, TypeMismatch):
            return self.path == x.path

        else:
            return False

    def __str__(self) -> str:
        return f'<TypeMismatch path={self.path}>'

    @property
    def path(self) -> Path:
        return self.__path


class UnsupportedDecoding(Exception):
    def __init__(self, path: Path) -> None:
        self.__path = path

    def __eq__(self, x: Any) -> bool:
        if isinstance(x, UnsupportedDecoding):
            return self.path == x.path

        else:
            return False

    def __str__(self) -> str:
        return f'<UnsupportedDecoding path={self.path}>'

    @property
    def path(self) -> Path:
        return self.__path


class ExternalSerializerException(Exception):
    def __init__(self, path: Path, exception: Exception) -> None:
        self.__path = path
        self.exception = exception

    def __eq__(self, x: Any) -> bool:
        if isinstance(x, ExternalSerializerException):
            return self.path == x.path
        else:
            return False

    def __str__(self) -> str:
        return f"<ExternalSerializerException path={self.path}>"

    @property
    def path(self) -> Path:
        return self.__path


FailureReason = Union[TypeMismatch, UnsupportedDecoding, ExternalSerializerException]


class DecodingError(Exception):
    def __init__(self, reason: FailureReason) -> None:
        self.__reason = reason

    def __eq__(self, x: Any) -> bool:
        if isinstance(x, DecodingError):
            return self.reason == x.reason
        else:
            return False

    def __str__(self) -> str:
        return f"<DecodingError reason={self.reason}>"

    @property
    def reason(self) -> FailureReason:
        return self.__reason
