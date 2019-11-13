"""Utilities."""
import functools
import inspect
import itertools
import re
from typing import (Any, Callable, Dict, List, Optional, Set, Type, Union,
                    cast, get_type_hints)

import falcon

from falcontyping.typedjson import args_of, origin_of, register_type

from .exceptions import TypeValidationError
from .resource import HTTPMethodAnnotation, TypedResource
from .types_ import Body as BodyParameter
from .types_ import Path as PathParameter
from .types_ import Query as QueryParameter

try:
    from typing_extensions import Protocol

    class ResourceMethodWithoutReturnValue(Protocol):

        def __call__(self, request: falcon.Request, response: falcon.Response, **kwargs: Any) -> None:  # pragma: no cover # noqa
            ...

    class ResourceMethodWithReturnValue(Protocol):

        def __call__(self, request: falcon.Request, response: falcon.Response, **kwargs: Any) -> Any:  # pragma: no cover # noqa
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

_HTTP_VERBS_WITH_BODIES = {'on_post', 'on_put', 'on_patch'}


def is_supported_request_type(type_: Any) -> bool:
    """Check if type is a supported type for serialization/deserialization."""
    if isinstance(type_, QueryParameter) or isinstance(type_, BodyParameter):
        type_ = type_.wrapped_type

    has_supported_parent = any(
        issubclass(type_, parent) for parent in _AVAILABLE_EXTERNAL_SCHEMA_PRODIVERS
    )

    return (has_supported_parent or type_ == type(None)) and type_ is not Any  # noqa


def is_supported_response_type(type_: Any) -> bool:
    """Check if type is a supported type for serialization/deserialization."""
    has_supported_parent = any(
        issubclass(type_, parent) for parent in _AVAILABLE_EXTERNAL_SCHEMA_PRODIVERS
    )

    return (has_supported_parent or type_ == type(None)) and type_ is not Any  # noqa


def validate_type_preconditions(type_: Any, type_checker: Callable[..., bool]) -> None:
    """Validate that used type hints are supported."""
    if len(_AVAILABLE_EXTERNAL_SCHEMA_PRODIVERS) == 0:
        raise TypeValidationError('No schema provider is installed. You need to install either Marshmallow or Pydantic')

    def predicate(type_: Any) -> bool:
        """Check if type can be used in the body of the request or response."""
        origin, args = origin_of(type_), args_of(type_)

        if origin is Union:
            return all(predicate(arg) for arg in args)

        else:
            return type_checker(type_)

    error = ('Resource methods must accept/return either Nothing, '
             'marshmallow.Schema or pydantic.BaseModel not {}')

    try:
        if type_ and not predicate(type_):
            raise TypeValidationError(error.format(type_))

    except TypeError:
        raise TypeValidationError(error.format(type_))


def validate_method_signature(method: ResourceMethodWithReturnValue,
                              path_parameters_names: Set[str]) -> HTTPMethodAnnotation:
    """
    Validate whether resource method has the right signature.

    :returns: request and response hints.
    """
    hints, arguments = get_type_hints(method), inspect.getfullargspec(method).args

    validate_type_preconditions(hints.get('return', None), type_checker=is_supported_response_type)

    for parameter in filter(lambda p: hints.get(p, None) is Any or p not in arguments, path_parameters_names):
        raise TypeValidationError(f'Path parameter {parameter} has type hint Any or is missing from signature')

    if len(arguments) < 3:
        raise TypeValidationError('Every resource method must have the first two parameters as '
                                  'falcon.Request and falcon.Response')

    if hints.get(arguments[1], Any) not in [falcon.Request, Any]:
        raise TypeValidationError('First parameter must be of type falcon.Request')

    if hints.get(arguments[2], Any) not in [falcon.Response, Any]:
        raise TypeValidationError('Second parameter must be of type falcon.Response')

    non_path_parameters_names: Set[str] = set(arguments) - (path_parameters_names |  # noqa
                                                            set(itertools.islice(arguments, 3)) | set(['return']))

    path_parameters: List[PathParameter] = []

    for name in filter(hints.get, path_parameters_names):
        register_type(hints[name])

        path_parameters.append(PathParameter(hints[name], name=name))

    non_path_parameters: Dict[Union[Type[QueryParameter], Type[BodyParameter]],
                              Union[QueryParameter, BodyParameter]] = {}

    for name in non_path_parameters_names:
        hint = hints.get(name, None)

        validate_type_preconditions(hint, type_checker=is_supported_request_type)

        parameter_type: Union[Type[QueryParameter], Type[BodyParameter]]

        if isinstance(hint, QueryParameter) or isinstance(hint, BodyParameter):
            parameter_type = type(hint)

        else:
            # This parameter is neither a query or body parameter
            # We will assume that POST, PUT and PATCH only have bodies and
            # other methods only have query parameters.
            #
            # If the user needs to have methods that accepts both body and request parameters
            # Query and Body annotations can be used.
            #
            # An error will be raised in ambiguous situations nevertheless.
            if method.__name__.lower() in _HTTP_VERBS_WITH_BODIES:  # type: ignore
                parameter_type = BodyParameter

            else:
                parameter_type = QueryParameter

        if parameter_type in non_path_parameters:
            raise TypeValidationError('There can not be more than one body parameter and one query paremeter. '
                                      'To specify both a query and a body parameter use Query and Body annotations. '
                                      'Did you forget to add a path parameter to resource route /{%s} ?' % name)

        non_path_parameters[parameter_type] = parameter_type(hint, name=name)  # type: ignore

    return HTTPMethodAnnotation(path=path_parameters,

                                query=cast(Optional[QueryParameter], non_path_parameters.get(QueryParameter)),
                                body=cast(Optional[BodyParameter], non_path_parameters.get(BodyParameter)),

                                returns=hints.get('return'))


def patch_resource_methods(uri_template: str, resource: TypedResource) -> None:
    """Patch resource methods to add type hint supports."""
    path_parameters = set(match.group('fname') for match in _FIELD_PATTERN.finditer(uri_template))

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

    for method_name in filter(functools.partial(hasattr, resource), _METHOD_NAMES):
        method: ResourceMethodWithReturnValue = getattr(resource, method_name)

        if not callable(method):
            raise TypeValidationError(f'{resource}.{method_name} must be a Callable')

        try:
            annotation = validate_method_signature(method, path_parameters_names=path_parameters)

            resource._init_annotations()
            resource._set_method_annotations(method_name, annotation)

        except TypeValidationError as e:
            raise TypeValidationError(f'{resource}.{method} raised: {e}')

        setattr(resource, method_name, resource_method_wrapper(method))
