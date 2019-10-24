# Falcon typing

![PyPI - Python Version](https://img.shields.io/pypi/pyversions/falcontyping)
![PyPI](https://img.shields.io/pypi/v/falcontyping)
[![codecov](https://codecov.io/gh/abdelrahman-t/falcontyping/branch/master/graph/badge.svg)](https://codecov.io/gh/abdelrahman-t/falcontyping)
[![Build Status](https://travis-ci.org/abdelrahman-t/falcontyping.svg?branch=master)](https://travis-ci.org/abdelrahman-t/falcontyping)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

### Use type hints to specify request parameters with Marshmallow and Pydantic support.
**Uses [typedjson](https://github.com/mitsuse/typedjson-python)

### Example
```python
"""API."""
from typing import Optional, Union

from pydantic import BaseModel as PydanticModel
from falcontyping import TypedAPI, TypedResource


class UserV1(PydanticModel):

    username: str

class UserV2(PydanticModel):

    username: str
    balance: float


class UsersResource(TypedResource):

    def on_post(self, request, response, user: Union[UserV2, UserV1]) -> Union[UserV2, UserV1]:
        if isinstance(user, UserV2):
            return UserV2(username=user.username, balance=user.balance)

        else:
            return UserV1(username=user.username)

class UserDetailsResource(TypedResource):

    def on_get(self, request, response, user_id: int) -> Optional[Union[UserV2, UserV1]]:
        if user_id == 2:
            return UserV2(username='user', balance=0.0)

        if user_id == 1:
            return UserV1(username='user')

        return None

API = TypedAPI()
API.add_route('/users', UserResource())
API.add_route('/users/{user_id}', UserDetailsResource())
```

### How to install
`pip install falcontyping`
