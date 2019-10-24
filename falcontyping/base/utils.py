"""Utilities."""
import functools
import inspect
import itertools
import re
from typing import (Any, Callable, Dict, List, Optional, Set, Tuple, Union,
                    get_type_hints)

import falcon

from falcontyping.typedjson import args_of, origin_of

from .exceptions import TypeValidationError

try:
    from typing_extensions import Protocol

    class ResourceMethodWithoutReturnValue(Protocol):

        def __call__(self, request: falcon.Request, respone: falcon.Response, **kwargs: Any) -> None:  # pragma: no cover
            ...

    class ResourceMethodWithReturnValue(Protocol):

        def __call__(self, request: falcon.Request, respone: falcon.Response, **kwargs: Any) -> Any:  # pragma: no cover
            ...

except ImportError:  # pragma: no cover
    ResourceMethodWithoutReturnValue = Callable  # type: ignore # pragma: no cover
    ResourceMethodWithReturnValue = Callable     # type: ignore # pragma: no cover

try:
    from pydantic import BaseModel as PydanticBaseModel

except ImportError:
    PydanticBaseModel = None  # type: ignore


try:
    from marshmallow import Schema as MarshmallowSchema

except ImportError:
    MarshmallowSchema = None  # type: ignore


_AVAILABLE_EXTERNAL_SCHEMA_PRODIVERS = set(
    filter(None, [MarshmallowSchema, PydanticBaseModel])
)

# Taken from https://github.com/falconry/falcon/blob/master/falcon/routing/compiled.py#L27
_FIELD_PATTERN = re.compile(
    # NOTE(kgriffs): This disallows the use of the '}' character within
    # an argstr. However, we don't really have a way of escaping
    # curly brackets in URI templates at the moment, so users should
    # see this as a similar restriction and so somewhat unsurprising.
    #
    # We may want to create a contextual parser at some point to
    # work around this problem.
    r'{((?P<fname>[^}:]*)((?P<cname_sep>:(?P<cname>[^}\(]*))(\((?P<argstr>[^}]*)\))?)?)}'
)

_METHOD_NAMES: List[str] = [
    'on_%s' % method for method in ('get', 'post', 'put', 'patch', 'delete', 'head', 'options')
]


def validate_type_preconditions(type_: Any) -> None:
    """Validate that used type hints are supported."""
    if len(_AVAILABLE_EXTERNAL_SCHEMA_PRODIVERS) == 0:
        raise TypeValidationError('No schema provider is installed. You need to install either Marshmallow or Pydantic')

    error = ('Resource methods must accept/return either Nothing, '
             'marshmallow.Schema or pydantic.BaseModel not {}')

    def predicate(type_: Any) -> bool:
        """Check if type can be used in the body of the request or response."""
        origin, args = origin_of(type_), args_of(type_)

        if origin is Union:
            return all(predicate(arg) for arg in args)

        else:
            has_supported_parent = any(
                issubclass(type_, parent) for parent in _AVAILABLE_EXTERNAL_SCHEMA_PRODIVERS
            )
            return (has_supported_parent or type_ == type(None)) and type_ is not Any  # noqa

    try:
        if type_ and not predicate(type_):
            raise TypeValidationError(error.format(type_))

    except TypeError:
        raise TypeValidationError(error.format(type_))


def validate_method_signature(method: ResourceMethodWithReturnValue, uri_parameters: Set[str]) -> Tuple[Optional[str],
                                                                                                        Dict]:
    """
    Validate whether resource method has the right signature.

    :returns: body parameter name and hints
    """
    hints = get_type_hints(method)
    arguments = inspect.getfullargspec(method).args

    for parameter in filter(lambda p: hints.get(p, None) is Any or p not in arguments, uri_parameters):
        raise TypeValidationError(f'URI parameter {parameter} has type hint Any or is missing from signature')

    validate_type_preconditions(
        hints.get('return', None)
    )

    if len(arguments) < 3:
        raise TypeValidationError('Every resource method must have the first two parameters as '
                                  'falcon.Request and falcon.Response')

    if hints.get(arguments[1], Any) not in [falcon.Request, Any]:
        raise TypeValidationError('First parameter must be of type falcon.Request')

    if hints.get(arguments[2], Any) not in [falcon.Response, Any]:
        raise TypeValidationError('Second parameter must be of type falcon.Response')

    body_parameters = set(arguments) - (uri_parameters | set(itertools.islice(arguments, 3)) | set(['return']))

    if len(body_parameters) > 1 and any(hints.get(parameter) for parameter in body_parameters):
        raise TypeValidationError('Any resource method can not accept more than one request parameter, that is one'
                                  'parameter of type marshmallow.Schema or pydantic.BaseModel')

    for parameter_name in body_parameters:
        validate_type_preconditions(hints.get(parameter_name, None))

    return next(iter(body_parameters & set(hints)), None), hints


def patch_resource_methods(uri_template: str, resource: Any) -> None:
    """Patch resource methods to add type hint supports."""
    uri_parameters = set(match.group('fname') for match in _FIELD_PATTERN.finditer(uri_template))

    def resource_method_wrapper(method: ResourceMethodWithReturnValue) -> ResourceMethodWithoutReturnValue:
        """
        Wraps resource methods.

        This function will takes whatever is returned by resource methods and assigns
        it to response.media.
        """
        @functools.wraps(method)
        def curried(request: falcon.Request, response: falcon.Response, **kwargs: Any) -> None:
            media = method(request, response, **kwargs)

            if media:
                response.media = media

        return curried

    resource.methods_body_parameter = {}
    resource.hints = {}

    for method_name in filter(functools.partial(hasattr, resource), _METHOD_NAMES):

        method: ResourceMethodWithReturnValue = getattr(resource, method_name)

        if not callable(method):
            raise TypeValidationError(f'{resource}.{method_name} must be a Callable')

        try:
            body_parameter, hints = validate_method_signature(method, uri_parameters=uri_parameters)

            resource.methods_body_parameter[method_name] = body_parameter
            resource.hints[method_name] = hints

        except TypeValidationError as e:
            raise TypeValidationError(f'{resource}.{method} raised: {e}')

        wrapped = resource_method_wrapper(method)

        setattr(resource, method_name, wrapped)
