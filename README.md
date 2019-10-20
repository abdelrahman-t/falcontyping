# Falcon typing

### Use type hints to specify request parameters with Marshmallow and Pydantic support.
Uses [typedjson](https://github.com/mitsuse/typedjson-python)

### Example
```
"""API."""
from typing import Union

import falcon

# Import Marshmallow
from marshmallow import Schema as MarhmallowSchema
from marshmallow import fields

# Import Pydantic
from pydantic import BaseModel as PydanticModel
from pydantic import ValidationError

from falcontyping import TypedAPI, TypedResource, TypingMiddleware

# Add typing support to Falcon
API = falcon.API(middleware=[TypingMiddleware()])
API = TypedAPI(API)


class UserPydantic(PydanticModel):

    username: str


class UserMarshmallow(MarhmallowSchema):

    username = fields.String()


class UserResource(TypedResource):

    # A rather contrived example
    def on_post(self, request, response,
                # Specify query parameter type hint
                _id : int,
                # Specify body parameter type hint
                user: Union[UserPydantic, UserMarshmallow]) -> Union[UserPydantic, UserMarshmallow]:
    
        return UserMarshmallow().load({'username': user.username})


API.add_route('/users/{_id}', UserResource())
```

### How to install
`pip install falcontyping`
