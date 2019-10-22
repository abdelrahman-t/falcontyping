"""API wrapper."""
from typing import Any

import falcon
import wrapt

from ..middleware import TypingMiddleware
from .resource import TypedResource
from .utils import patch_resource_methods


class TypedAPI(wrapt.ObjectProxy):
    """Transparent proxy over falcon.API."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        middleware = kwargs.get('middleware', [])

        if not any(isinstance(m, TypingMiddleware) for m in middleware):
            kwargs = {**kwargs, 'middleware': middleware + [TypingMiddleware()]}

        super().__init__(
            falcon.API(*args, **kwargs)
        )

    def add_route(self, uri_template: str, resource: Any, **kwargs: Any) -> Any:
        """Extract type hints information before adding route."""
        if isinstance(resource, TypedResource):
            patch_resource_methods(uri_template, resource)

        return self.__wrapped__.add_route(uri_template, resource, **kwargs)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.__wrapped__.__call__(*args, **kwargs)
