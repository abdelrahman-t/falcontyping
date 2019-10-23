"""Tests."""
import falcon
import pytest
from pydantic import BaseModel

from . import TypedAPI, TypedResource
from .base.exceptions import TypeValidationError


class Model(BaseModel):

    field: int


class TestValidation:

    class InvalidResourceWithQueryParameter1(TypedResource):

        # Invalid because it because it is missing query parameter
        def on_get(self, request, response, request_parameter: int) -> int:
            pass

    class InvalidResourceWithQueryParameter2(TypedResource):

        # Invalid because it because it returns an invalid type
        def on_post(self, request, response, query_parameter, request_parameter: int) -> int:
            pass

    class InvalidResourceWithQueryParameter3(TypedResource):

        # Invalid because it takes an invalid type as a request parameter
        def on_delete(self, request, response, query_parameter, request_parameter: int) -> Model:
            pass

    class InvalidResourceWithoutQueryParameter1(TypedResource):

        # Invalid because user forgot to specify query parameter when adding route,
        # and now query_parameter is treated as a request parameter
        def on_delete(self, request, response, query_parameter: int, request_parameter: Model) -> Model:
            pass

    class ValidResourceWithQueryParameter1(TypedResource):

        # A method with no argument and no annotations
        def on_get(self, request, response, query_parameter):
            pass

    class ValidResourceWithQueryParameter2(TypedResource):

        # A method with no arguments but with annotations
        def on_post(self, request: falcon.Request, response: falcon.Response, query_parameter) -> None:
            pass

    class ValidResourceWithQueryParameter3(TypedResource):

        # A method with no query parameter annotation
        def on_delete(self, request: falcon.Request, response: falcon.Response, query_parameter) -> Model:
            pass

    class ValidResourceWithQueryParameter4(TypedResource):

        # A method with only query parameters
        def on_patch(self, request, response, query_parameter: int) -> None:
            pass

    class ValidResourceWithQueryParameter5(TypedResource):

        # A method with a mix of annotated and non-annotated arguments
        def on_put(self, request, response, field: Model, query_parameter: int, another_field) -> Model:
            pass

    def test_invalid_resource_with_query_parameters(self):

        with pytest.raises(TypeValidationError):
            TypedAPI().add_route('/resource/{query_parameter}', self.InvalidResourceWithQueryParameter1())

        with pytest.raises(TypeValidationError):
            TypedAPI().add_route('/resource/{query_parameter}', self.InvalidResourceWithQueryParameter2())

        with pytest.raises(TypeValidationError):
            TypedAPI().add_route('/resource/{query_parameter}', self.InvalidResourceWithQueryParameter3())

        with pytest.raises(TypeValidationError):
            TypedAPI().add_route('/resource/{query_parameter}', self.InvalidResourceWithQueryParameter1())

        with pytest.raises(TypeValidationError):
            TypedAPI().add_route('/resource/{query_parameter}', self.InvalidResourceWithQueryParameter1())

    def test_invalid_resource_without_query_parameters(self):

        with pytest.raises(TypeValidationError):
            TypedAPI().add_route('/resource', self.InvalidResourceWithoutQueryParameter1())

    def test_valid_resource_with_query_parameters(self):

        TypedAPI().add_route('/resource/{query_parameter}', self.ValidResourceWithQueryParameter1())
        TypedAPI().add_route('/resource/{query_parameter}', self.ValidResourceWithQueryParameter2())
        TypedAPI().add_route('/resource/{query_parameter}', self.ValidResourceWithQueryParameter3())
        TypedAPI().add_route('/resource/{query_parameter}', self.ValidResourceWithQueryParameter4())
        TypedAPI().add_route('/resource/{query_parameter}', self.ValidResourceWithQueryParameter5())
