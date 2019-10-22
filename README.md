# Falcon typing

![PyPI - Python Version](https://img.shields.io/pypi/pyversions/falcontyping)
![PyPI](https://img.shields.io/pypi/v/falcontyping)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

### Use type hints to specify request parameters with Marshmallow and Pydantic support.
Uses [typedjson](https://github.com/mitsuse/typedjson-python)

### Example
```python
"""API."""
from typing import Union

from marshmallow import Schema as MarhmallowSchema
from marshmallow import fields
from pydantic import BaseModel as PydanticModel

# Create API
from falcontyping import TypedAPI, TypedResource
API = TypedAPI()


class UserV1(MarhmallowSchema):

    username = fields.String()


class UserV2(PydanticModel):

    username: str


class UserResource(TypedResource):

    def on_post(self, request, response, user: Union[UserV1, UserV2]) -> Union[UserV1, UserV2]:
        if isinstance(user, UserV1):
            return UserV1().load({'username': user.username})

        else:
            return UserV2(username=user.username)


class UserDetailsResource(TypedResource):

    def on_get(self, request, response, user_id: int) -> UserV2:
        return UserV2(username='user')


API.add_route('/users', UserResource())
API.add_route('/users/{user_id}', UserDetailsResource())
```

### How to install
`pip install falcontyping`
