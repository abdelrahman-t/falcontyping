"""Typing middleware."""
from operator import attrgetter
from typing import Any, Callable, Dict, Optional

import falcon
from falcon import Request, Response

from falcontyping.base import (PydanticBaseModel, TypedResource,
                               TypeValidationError)
from falcontyping.typedjson import DecodingError, ExternalSerializerException
from falcontyping.typedjson import decode as decode_using_hints

_VALID_RESPONSE_TYPES = set([PydanticBaseModel, dict, type(None)])


class TypingMiddleware:

    @staticmethod
    def _decode_or_raise_error(hint: Any, parameter: Any) -> Any:
        """
        Decode value using type hint or fail.

        :raises: falcon.HTTPError or ExternalSerializerException
        """
        result = decode_using_hints(hint, parameter)

        if isinstance(result, DecodingError):
            if isinstance(result.reason, ExternalSerializerException):
                raise falcon.HTTPError(status=falcon.HTTP_UNPROCESSABLE_ENTITY,  # pylint: disable=no-member
                                       description=str(result.reason.exception))

            else:
                raise falcon.HTTPError(status=falcon.HTTP_UNPROCESSABLE_ENTITY,  # pylint: disable=no-member
                                       description=f'\'{parameter}\' must be of type {hint} not {type(parameter)}')

        return result

    def process_request(self, request: Request, response: Response) -> None:
        """
        Process the request before routing it.

        Because Falcon routes each request based on req.path, a
        request can be effectively re-routed by setting that
        attribute to a new value from within process_request().

        :param request: Request object that will eventually be
            routed to an on_* responder method.
        :param response: Response object that will be routed to
            the on_* responder.
        """
        ...

    def process_resource(self, request: Request, response: Response, resource: Any, parameters: Dict) -> None:
        """
        Process the request after routing.

        This method is only called when the request matches
        a route to a resource.

        :param request: Request object that will be passed to the
            routed responder.
        :param response: Response object that will be passed to the
            responder.
        :param resource: Resource object to which the request was
            routed.
        :param parameters: A dict-like object representing any additional
            parameters derived from the route's URI template fields,
            that will be passed to the resource's responder
            method as keyword arguments.
        """
        if not isinstance(resource, TypedResource):
            return

        method = 'on_%s' % request.method.lower()
        handler: Optional[Callable] = getattr(resource, method, None)

        if handler is None:
            return

        annotations = resource.annotations[method]

        for path_parameter in filter(attrgetter('is_usable'), annotations.path):
            value = parameters.get(path_parameter.name)

            if value is None:
                raise falcon.HTTPBadRequest(  # pylint: disable=no-member
                    f'Path parameter {path_parameter.name} must be specified')

            parameters[path_parameter.name] = self._decode_or_raise_error(path_parameter.wrapped_type, value)

        if annotations.query and annotations.query.is_usable:
            query_parameter = annotations.query

            parameters[query_parameter.name] = self._decode_or_raise_error(query_parameter.wrapped_type,
                                                                           request.params)

        if annotations.body and annotations.body.is_usable:
            body_parameter = annotations.body

            parameters[body_parameter.name] = self._decode_or_raise_error(body_parameter.wrapped_type,
                                                                          request.media)

    def process_response(self, request: Request, response: Response, resource: Any, request_succeeded: bool) -> None:
        """
        Post-processing of the response (after routing).

        :param request: Request object.
        :param response: Response object.
        :param resource: Resource object to which the request was routed.
            May be None if no route was found for the request.

        :param request_succeeded: True if no exceptions were raised while the framework processed and
            routed the request; otherwise False.
        """
        if not(request_succeeded and isinstance(resource, TypedResource)):
            return

        method = 'on_%s' % request.method.lower()

        handler: Optional[Callable] = getattr(resource, method, None)
        returns: Any = resource.annotations[method].returns

        if returns:
            media = getattr(response, 'media', None)
            media = decode_using_hints(returns, media)

            if not any(isinstance(media, type_) for type_ in _VALID_RESPONSE_TYPES):  # type: ignore
                raise TypeValidationError(f'{resource}.{handler} returned a unexpected value. ',
                                          f'Resource methods must return either Nothing, '
                                          f'marshmallow.Schema or pydantic.BaseModel not {type(media)}')

            if isinstance(media, PydanticBaseModel):
                media = media.dict()

            response.media = media
