"""Typing middleware."""
from typing import Any, Callable, Dict, Optional, get_type_hints

import falcon
from falcon import Request, Response

from falcontyping.base import (MarshmallowSchema, PydanticBaseModel,
                               TypedResource, TypeValidationError,
                               schema_providers)
from falcontyping.typedjson import DecodingError, ExternalSerializerException
from falcontyping.typedjson import decode as decode_using_hints

_VALID_RESPONSE_TYPES = schema_providers | set([dict])


class TypingMiddleware:

    @staticmethod
    def _decode_or_raise_error(hint: Any, parameter: Any) -> Any:
        """
        Decode value using type hint or fail.

        :raises: falcon.HTTPError
        """
        result = decode_using_hints(hint, parameter)

        if isinstance(result, DecodingError):
            if isinstance(result.reason, ExternalSerializerException):
                raise result.reason.exception from None

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

        handler: Optional[Callable] = getattr(resource, 'on_%s' % request.method.lower(), None)

        if handler:
            # Get hints for only those variables that should be passed to the request handler.
            hints = get_type_hints(handler)

            # Decode values using type hints, All values in parameters will be based as
            # Keyword arguments to the request handler.
            for parameter in parameters:
                parameters[parameter] = self._decode_or_raise_error(hints[parameter], parameters.get(parameter))

            # Decode body parameter if there is one.
            body_parameter = resource.methods_body_parameters[handler.__name__]
            if body_parameter:
                parameters[body_parameter] = self._decode_or_raise_error(hints[body_parameter],
                                                                         getattr(request, 'media', None))

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

        if handler:
            # Get type hint for the return type of the request handler.
            hint: Any = get_type_hints(handler)['return']

            # Decode returned value using the "return" type hint.
            media = getattr(response, 'media', None)
            media = decode_using_hints(hint, media)

            if isinstance(media, DecodingError):
                raise TypeValidationError(
                    f'{resource}.{handler} returned a value of type {media}:{type(media)} instead of {hint}')

            if media is None:
                ...

            else:
                if not any(isinstance(media, type_) for type_ in _VALID_RESPONSE_TYPES):
                    raise TypeValidationError(f'{resource}.{handler} returned a unexpected value. ',
                                              f'Resource methods must return either Nothing, '
                                              f'marshmallow.Schema or pydantic.BaseModel not {type(media)}')

                try:
                    if isinstance(media, dict):
                        ...

                    elif isinstance(media, PydanticBaseModel):
                        media = media.dict()

                    elif isinstance(media, MarshmallowSchema):
                        media = hint().dump(media)

                    response.media = media

                except Exception:
                    raise TypeValidationError(f'{resource}.{handler} '
                                              f'failed to serialize {media}:{type(media)} to JSON.')
