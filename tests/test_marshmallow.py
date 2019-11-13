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

    class InvalidResourceWithPathParameter1(TypedResource):

        # Invalid because it because it is missing path parameter
        def on_get(self, request, response, request_parameter: int) -> int:
            pass

    class InvalidResourceWithPathParameter2(TypedResource):

        # Invalid because it because it returns an invalid type
        def on_post(self, request, response, path_parameter, request_parameter: int) -> int:
            pass

    class InvalidResourceWithPathParameter3(TypedResource):

        # Invalid because it takes an invalid type as a request parameter
        def on_delete(self, request, response, path_parameter, request_parameter: int) -> Model:
            pass

    class InvalidResourceWithPathParameter4(TypedResource):

        # Invalid because it takes more than one request parameter
        def on_delete(self, request, response, path_parameter, request_parameter: Model, other: Model) -> Model:
            pass

    class InvalidResourceWithPathParameter5(TypedResource):

        # Invalid because it is missing one path parameter from route or has an extra request parameter
        def on_delete(self, request, response, path_parameter, request_parameter: Model, extra_parameter) -> Model:
            pass

    class InvalidResourceWithPathParameter6(TypedResource):

        # Invalid because it violates protocol
        def on_delete(self, request: int, response, path_parameter) -> Model:
            pass

    class InvalidResourceWithPathParameter7(TypedResource):

        # Invalid because it violates protocol
        def on_delete(self, request, response: int, path_parameter) -> Model:
            pass

    class InvalidResourceWithPathParameter8(TypedResource):

        # Invalid because it violates protocol
        on_delete = None

    class InvalidResourceWithoutPathParameter1(TypedResource):

        # Invalid because user forgot to specify path parameter when adding route,
        # and now path_parameter is treated as a request parameter
        def on_delete(self, request, response, path_parameter: int, request_parameter: Model) -> Model:
            pass

    class ValidResourceWithPathParameter1(TypedResource):

        # A method no request parameter and no annotations
        def on_get(self, request, response, path_parameter):
            pass

    class ValidResourceWithPathParameter2(TypedResource):

        # A method no request parameter but with annotations
        def on_post(self, request: falcon.Request, response: falcon.Response, path_parameter) -> None:
            pass

    class ValidResourceWithPathParameter3(TypedResource):

        # A method with no path parameter annotation
        def on_delete(self, request: falcon.Request, response: falcon.Response, path_parameter) -> Model:
            pass

    class ValidResourceWithPathParameter4(TypedResource):

        # A method with only path parameters
        def on_patch(self, request, response, path_parameter: int) -> None:
            pass

    class ValidResourceWithPathParameter5(TypedResource):

        # A method with a mix of annotated and non-annotated arguments
        def on_put(self, request, response, field: Model, path_parameter: int) -> Model:
            pass

    def test_invalid_resource_with_path_parameters(self):

        with pytest.raises(TypeValidationError):
            TypedAPI().add_route('/resource/{path_parameter}', self.InvalidResourceWithPathParameter1())

        with pytest.raises(TypeValidationError):
            TypedAPI().add_route('/resource/{path_parameter}', self.InvalidResourceWithPathParameter2())

        with pytest.raises(TypeValidationError):
            TypedAPI().add_route('/resource/{path_parameter}', self.InvalidResourceWithPathParameter3())

        with pytest.raises(TypeValidationError):
            TypedAPI().add_route('/resource/{path_parameter}', self.InvalidResourceWithPathParameter4())

        with pytest.raises(TypeValidationError):
            TypedAPI().add_route('/resource/{path_parameter}', self.InvalidResourceWithPathParameter5())

        with pytest.raises(TypeValidationError):
            TypedAPI().add_route('/resource/{path_parameter}', self.InvalidResourceWithPathParameter6())

        with pytest.raises(TypeValidationError):
            TypedAPI().add_route('/resource/{path_parameter}', self.InvalidResourceWithPathParameter7())

        with pytest.raises(TypeValidationError):
            TypedAPI().add_route('/resource/{path_parameter}', self.InvalidResourceWithPathParameter8())

        with pytest.raises(TypeValidationError):
            TypedAPI().add_route('/resource/{path_parameter}', self.InvalidResourceWithPathParameter1())

        with pytest.raises(TypeValidationError):
            TypedAPI().add_route('/resource/{path_parameter}', self.InvalidResourceWithPathParameter1())

    def test_invalid_resource_without_path_parameters(self):

        with pytest.raises(TypeValidationError):
            TypedAPI().add_route('/resource', self.InvalidResourceWithoutPathParameter1())

    def test_valid_resource_with_path_parameters(self):

        TypedAPI().add_route('/resource/{path_parameter}', self.ValidResourceWithPathParameter1())
        TypedAPI().add_route('/resource/{path_parameter}', self.ValidResourceWithPathParameter2())
        TypedAPI().add_route('/resource/{path_parameter}', self.ValidResourceWithPathParameter3())
        TypedAPI().add_route('/resource/{path_parameter}', self.ValidResourceWithPathParameter4())
        TypedAPI().add_route('/resource/{path_parameter}', self.ValidResourceWithPathParameter5())


class TestMiddleware:

    @pytest.fixture()
    def API(self):
        _API = TypedAPI()
        _API.add_route('/resource1/{path_parameter}', self.ValidResourceWithPathParameter1())
        _API.add_route('/resource2/{path_parameter}', self.ValidResourceWithPathParameter2())
        _API.add_route('/resource3/{path_parameter}', self.ValidResourceWithPathParameter3())
        _API.add_route('/resource4/{path_parameter}', self.ValidResourceWithPathParameter4())
        _API.add_route('/resource5/{path_parameter}', self.ValidResourceWithPathParameter5())
        _API.add_route('/resource6/{path_parameter}', self.ValidResourceWithPathParameter6())
        _API.add_route('/resource7/{path_parameter}', self.ValidResourceWithPathParameter7())
        _API.add_route('/resource8/{path_parameter}', self.ValidResourceWithPathParameter8())
        _API.add_route('/resource9/{path_parameter}', self.ValidResourceWithPathParameter9())
        _API.add_route('/resource10/{path_parameter}', self.ValidResourceWithPathParameter10())
        _API.add_route('/resource11/{path_parameter}', self.ValidResourceWithPathParameter11())
        _API.add_route('/resource12/{path_parameter}', self.ValidResourceWithPathParameter12())

        return falcon.testing.TestClient(_API)

    class ValidResourceWithPathParameter1(TypedResource):

        # A method with no request parameter and no annotations
        def on_post(self, request, response, path_parameter):
            ...

    class ValidResourceWithPathParameter2(TypedResource):

        # A method with no request parameter but with annotations
        def on_post(self, request: falcon.Request, response: falcon.Response, path_parameter) -> None:
            ...

    class ValidResourceWithPathParameter3(TypedResource):

        # A method with no path parameter annotation
        def on_post(self, request: falcon.Request, response: falcon.Response, path_parameter) -> Model:
            return dict(field=0)

    class ValidResourceWithPathParameter4(TypedResource):

        # A method with no path parameter annotation but with an unknown return type
        def on_post(self, request: falcon.Request, response: falcon.Response, path_parameter):
            response.media = {'key': 'value'}

    class ValidResourceWithPathParameter5(TypedResource):

        # A method with only path parameters
        def on_post(self, request, response, path_parameter: int) -> None:
            assert isinstance(path_parameter, int)

    class ValidResourceWithPathParameter6(TypedResource):

        # A method with a mix of annotated and non-annotated arguments
        def on_post(self, request, response, field: Model, path_parameter: int) -> Model:
            assert isinstance(path_parameter, int)
            Model().load(field)

            return field

    class ValidResourceWithPathParameter7(TypedResource):

        # A method with a mix of annotated and non-annotated arguments and multiple return types
        def on_post(self, request, response, field: Model, path_parameter: int) -> Union[Model, None]:
            assert isinstance(path_parameter, int)
            Model().load(field)

            return field

    class ValidResourceWithPathParameter8(TypedResource):

        # A method with a mix of annotated and non-annotated arguments and multiple return types
        def on_post(self, request, response, field: Model, path_parameter: int) -> Union[Model, None]:
            assert isinstance(path_parameter, int)
            Model().load(field)

            return None

    class ValidResourceWithPathParameter9(TypedResource):

        # A method with a mix of annotated and non-annotated arguments and multiple return types
        def on_post(self, request, response, field: Model, path_parameter: int) -> Union[None, Model, AnotherModel]:
            assert isinstance(path_parameter, int)
            Model().load(field)

            return dict(another_field=0)

    class ValidResourceWithPathParameter10(TypedResource):

        # Raises an error because user sends invalid payload
        def on_post(self, request, response, field: Model, path_parameter: int) -> Union[None, Model, AnotherModel]:
            assert isinstance(path_parameter, int)
            Model().load(field)

            return dict(another_field=0)

    class ValidResourceWithPathParameter11(TypedResource):

        # Raises an error because user sends invalid payload
        def on_post(self, request, response, field: Model, path_parameter: int) -> Union[None, Model, AnotherModel]:
            assert isinstance(path_parameter, int)
            assert Model().load(field)

            return dict(another_field=0)

    class ValidResourceWithPathParameter12(TypedResource):

        # A method that has correct annotations but returns a mismatching type.
        def on_post(self, request, response, field: Model, path_parameter: int) -> Union[Model, AnotherModel]:
            assert isinstance(path_parameter, int)
            Model().load(field)

            return None

    def test_resource_with_path_parameters(self, API):
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
