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

This is a modified version of the annotation module at:
https://github.com/mitsuse/typedjson-python/blob/master/typedjson/annotation.py

Author: Tomoya Kose <tomoya@mitsuse.jp>
Repository: https://github.com/mitsuse/typedjson-python
"""
from typing import Dict, Optional, Tuple, Type


def args_of(type_: Type) -> Tuple[Type, ...]:
    args = getattr(type_, "__args__", None)
    return tuple() if args is None else args  # type: ignore


def hints_of(type_: Type) -> Optional[Dict[str, Type]]:
    from typing import get_type_hints
    from copy import copy

    origin = origin_of(type_)
    args = args_of(type_)
    type__ = type_ if origin is None else origin
    mapping = dict(zip(parameters_of(type_), args))

    if hasattr(type__, "__init__"):
        annotations = get_type_hints(type__.__init__)
        if len(mapping) > 0:
            annotations_: Dict[str, Type] = {}
            for n, t in annotations.items():
                if n == "return":
                    continue
                t_ = mapping.get(t)
                if t_ is None:
                    return None
                else:
                    annotations_[n] = t_
            return annotations_
        else:
            annotations_ = copy(annotations)
            annotations_.pop("return", None)
            return annotations_
    else:
        return None


def origin_of(type_: Type) -> Optional[Type]:
    from typing import List
    from typing import Tuple

    origin = getattr(type_, "__origin__", None)

    # In Python 3.6, the origin of Tuple type is `List` but in Python 3.7 it is `list`.
    if origin is List:
        return list
    # In Python 3.6, the origin of Tuple type is `Tuple` but in Python 3.7 it is `tuple`.
    elif origin is Tuple:
        return tuple
    else:
        return origin  # type: ignore


def parameters_of(type_: Type) -> Tuple[Type, ...]:
    origin = origin_of(type_)
    if origin is None:
        return tuple()
    else:
        parameters = getattr(origin, "__parameters__", None)
        return tuple() if parameters is None else parameters  # type: ignore
