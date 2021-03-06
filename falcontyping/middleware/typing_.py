"""Typing middleware."""
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
                raise result.reason.exception from None

            else:
                raise falcon.HTTPError(status=falcon.HTTP_UNPROCESSABLE_ENTITY,  # pylint: disable=no-member
                                       description=f'\'{parameter}\' must be of type {hint} not {type(parameter)}')

        return result

    @staticmethod
    def _try_decode_query_or_body(request: falcon.Request, hint: Any) -> Any:
        """Decode values by looking for them in both URI and request body."""
        # An assumption is being made here, That only POST, PUT and PATCH can have bodies.
        if request.method.lower() in ['post', 'put', 'patch']:
            key = 'media'

        else:
            key = 'params'

        return TypingMiddleware._decode_or_raise_error(hint, getattr(request, key, None))

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

        handler: Optional[Callable] = getattr(resource, 'on_%s' % request.method.lower(), None)

        if handler:
            # Get hints for only those variables that should be passed to the request handler.
            hints = resource.hints[handler.__name__]

            # Decode values using type hints, All values in parameters will be based as
            # Keyword arguments to the request handler.
            for parameter in filter(hints.get, parameters):
                parameters[parameter] = self._decode_or_raise_error(hints[parameter], parameters.get(parameter))

            # Decode body parameter if there is one.
            body_parameter = resource.methods_body_parameter[handler.__name__]
            if body_parameter:
                parameters[body_parameter] = self._try_decode_query_or_body(request, hints[body_parameter])

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
        if not (isinstance(resource, TypedResource) and request_succeeded):
            return

        handler: Optional[Callable] = getattr(resource, 'on_%s' % request.method.lower(), None)
        # Get type hint for the return type of the request handler.
        hint: Any = resource.hints[handler.__name__].get('return') if handler else None

        if hint:
            media = getattr(response, 'media', None)
            media = decode_using_hints(hint, media)

            if not any(isinstance(media, type_) for type_ in _VALID_RESPONSE_TYPES):  # type: ignore
                raise TypeValidationError(f'{resource}.{handler} returned a unexpected value. ',
                                          f'Resource methods must return either Nothing, '
                                          f'marshmallow.Schema or pydantic.BaseModel not {type(media)}')

            if isinstance(media, PydanticBaseModel):
                media = media.dict()

            response.media = media
