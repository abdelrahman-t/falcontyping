"""API wrapper."""
from typing import Any

import falcon

from .resource import TypedResource
from .utils import patch_resource_methods


class TypedAPI:
    """
    Transparent proxy over falcon.API.

    Proxy adds a verification step which is applied before calls to falcon.API.add_route()
    """

    def __init__(self, api: falcon.API) -> None:
        self.api = api

    def add_route(self, uri_template: str, resource: Any, **kwargs: Any) -> Any:
        """Verify method signature for typed resources."""
        if isinstance(resource, TypedResource):
            patch_resource_methods(uri_template, resource)

        return self.api.add_route(uri_template, resource, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self.api, name)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.api.__call__(*args, **kwargs)
