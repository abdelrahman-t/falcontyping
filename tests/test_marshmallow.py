"""Tests."""
from typing import Union

import falcon
import falcon.testing
import pytest
from marshmallow import Schema, fields

from falcontyping import TypedAPI, TypedResource
from falcontyping.base.exceptions import TypeValidationError


class Model(Schema):

    field = fields.Integer()


class AnotherModel(Schema):

    another_field = fields.Integer()


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

    class InvalidResourceWithQueryParameter4(TypedResource):

        # Invalid because it takes more than one request parameter
        def on_delete(self, request, response, query_parameter, request_parameter: Model, other: Model) -> Model:
            pass

    class InvalidResourceWithQueryParameter5(TypedResource):

        # Invalid because it is missing one query parameter from route or has an extra request parameter
        def on_delete(self, request, response, query_parameter, request_parameter: Model, extra_parameter) -> Model:
            pass

    class InvalidResourceWithQueryParameter6(TypedResource):

        # Invalid because it violates protocol
        def on_delete(self, request: int, response, query_parameter) -> Model:
            pass

    class InvalidResourceWithQueryParameter7(TypedResource):

        # Invalid because it violates protocol
        def on_delete(self, request, response: int, query_parameter) -> Model:
            pass

    class InvalidResourceWithQueryParameter8(TypedResource):

        # Invalid because it violates protocol
        on_delete = None

    class InvalidResourceWithoutQueryParameter1(TypedResource):

        # Invalid because user forgot to specify query parameter when adding route,
        # and now query_parameter is treated as a request parameter
        def on_delete(self, request, response, query_parameter: int, request_parameter: Model) -> Model:
            pass

    class ValidResourceWithQueryParameter1(TypedResource):

        # A method no request parameter and no annotations
        def on_get(self, request, response, query_parameter):
            pass

    class ValidResourceWithQueryParameter2(TypedResource):

        # A method no request parameter but with annotations
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
        def on_put(self, request, response, field: Model, query_parameter: int) -> Model:
            pass

    def test_invalid_resource_with_query_parameters(self):

        with pytest.raises(TypeValidationError):
            TypedAPI().add_route('/resource/{query_parameter}', self.InvalidResourceWithQueryParameter1())

        with pytest.raises(TypeValidationError):
            TypedAPI().add_route('/resource/{query_parameter}', self.InvalidResourceWithQueryParameter2())

        with pytest.raises(TypeValidationError):
            TypedAPI().add_route('/resource/{query_parameter}', self.InvalidResourceWithQueryParameter3())

        with pytest.raises(TypeValidationError):
            TypedAPI().add_route('/resource/{query_parameter}', self.InvalidResourceWithQueryParameter4())

        with pytest.raises(TypeValidationError):
            TypedAPI().add_route('/resource/{query_parameter}', self.InvalidResourceWithQueryParameter5())

        with pytest.raises(TypeValidationError):
            TypedAPI().add_route('/resource/{query_parameter}', self.InvalidResourceWithQueryParameter6())

        with pytest.raises(TypeValidationError):
            TypedAPI().add_route('/resource/{query_parameter}', self.InvalidResourceWithQueryParameter7())

        with pytest.raises(TypeValidationError):
            TypedAPI().add_route('/resource/{query_parameter}', self.InvalidResourceWithQueryParameter8())

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


class TestMiddleware:

    @pytest.fixture()
    def API(self):
        _API = TypedAPI()
        _API.add_route('/resource1/{query_parameter}', self.ValidResourceWithQueryParameter1())
        _API.add_route('/resource2/{query_parameter}', self.ValidResourceWithQueryParameter2())
        _API.add_route('/resource3/{query_parameter}', self.ValidResourceWithQueryParameter3())
        _API.add_route('/resource4/{query_parameter}', self.ValidResourceWithQueryParameter4())
        _API.add_route('/resource5/{query_parameter}', self.ValidResourceWithQueryParameter5())
        _API.add_route('/resource6/{query_parameter}', self.ValidResourceWithQueryParameter6())
        _API.add_route('/resource7/{query_parameter}', self.ValidResourceWithQueryParameter7())
        _API.add_route('/resource8/{query_parameter}', self.ValidResourceWithQueryParameter8())
        _API.add_route('/resource9/{query_parameter}', self.ValidResourceWithQueryParameter9())
        _API.add_route('/resource10/{query_parameter}', self.ValidResourceWithQueryParameter10())
        _API.add_route('/resource11/{query_parameter}', self.ValidResourceWithQueryParameter11())
        _API.add_route('/resource12/{query_parameter}', self.ValidResourceWithQueryParameter12())

        return falcon.testing.TestClient(_API)

    class ValidResourceWithQueryParameter1(TypedResource):

        # A method with no request parameter and no annotations
        def on_post(self, request, response, query_parameter):
            ...

    class ValidResourceWithQueryParameter2(TypedResource):

        # A method with no request parameter but with annotations
        def on_post(self, request: falcon.Request, response: falcon.Response, query_parameter) -> None:
            ...

    class ValidResourceWithQueryParameter3(TypedResource):

        # A method with no query parameter annotation
        def on_post(self, request: falcon.Request, response: falcon.Response, query_parameter) -> Model:
            return dict(field=0)

    class ValidResourceWithQueryParameter4(TypedResource):

        # A method with no query parameter annotation but with an unknown return type
        def on_post(self, request: falcon.Request, response: falcon.Response, query_parameter):
            response.media = {'key': 'value'}

    class ValidResourceWithQueryParameter5(TypedResource):

        # A method with only query parameters
        def on_post(self, request, response, query_parameter: int) -> None:
            assert isinstance(query_parameter, int)

    class ValidResourceWithQueryParameter6(TypedResource):

        # A method with a mix of annotated and non-annotated arguments
        def on_post(self, request, response, field: Model, query_parameter: int) -> Model:
            assert isinstance(query_parameter, int)
            Model().load(field)

            return field

    class ValidResourceWithQueryParameter7(TypedResource):

        # A method with a mix of annotated and non-annotated arguments and multiple return types
        def on_post(self, request, response, field: Model, query_parameter: int) -> Union[Model, None]:
            assert isinstance(query_parameter, int)
            Model().load(field)

            return field

    class ValidResourceWithQueryParameter8(TypedResource):

        # A method with a mix of annotated and non-annotated arguments and multiple return types
        def on_post(self, request, response, field: Model, query_parameter: int) -> Union[Model, None]:
            assert isinstance(query_parameter, int)
            Model().load(field)

            return None

    class ValidResourceWithQueryParameter9(TypedResource):

        # A method with a mix of annotated and non-annotated arguments and multiple return types
        def on_post(self, request, response, field: Model, query_parameter: int) -> Union[None, Model, AnotherModel]:
            assert isinstance(query_parameter, int)
            Model().load(field)

            return dict(another_field=0)

    class ValidResourceWithQueryParameter10(TypedResource):

        # Raises an error because user sends invalid payload
        def on_post(self, request, response, field: Model, query_parameter: int) -> Union[None, Model, AnotherModel]:
            assert isinstance(query_parameter, int)
            Model().load(field)

            return dict(another_field=0)

    class ValidResourceWithQueryParameter11(TypedResource):

        # Raises an error because user sends invalid payload
        def on_post(self, request, response, field: Model, query_parameter: int) -> Union[None, Model, AnotherModel]:
            assert isinstance(query_parameter, int)
            assert Model().load(field)

            return dict(another_field=0)

    class ValidResourceWithQueryParameter12(TypedResource):

        # A method that has correct annotations but returns a mismatching type.
        def on_post(self, request, response, field: Model, query_parameter: int) -> Union[Model, AnotherModel]:
            assert isinstance(query_parameter, int)
            Model().load(field)

            return None

    def test_resource_with_query_parameters(self, API):
        assert API.simulate_post('/resource1/1').json is None
        assert API.simulate_post('/resource2/2').json is None

        assert API.simulate_post('/resource3/3').json == {'field': 0}
        assert API.simulate_post('/resource4/4').json == {'key': 'value'}
        assert API.simulate_post('/resource5/5')
        assert API.simulate_post('/resource6/6', json={'field': 0}).json == {'field': 0}
        assert API.simulate_post('/resource7/7', json={'field': 0}).json == {'field': 0}
        assert API.simulate_post('/resource8/8', json={'field': 0}).json is None
        assert API.simulate_post('/resource9/9', json={'field': 0}).json == {'another_field': 0}

        API.simulate_post('/resource10/not-an-int', json={'field': 0}).status == 422
        API.simulate_post('/resource11/11', json={'unknown-field': 0}).status == 422

        with pytest.raises(TypeValidationError):
            API.simulate_post('/resource12/12', json={'field': 0})
