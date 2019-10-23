"""API."""
from typing import Optional, Union

from pydantic import BaseModel as PydanticModel

from falcontyping import TypedAPI, TypedResource

API = TypedAPI()


class UserV1(PydanticModel):

    username: str


class UserV2(PydanticModel):

    username: str
    balance: float


class UserResource(TypedResource):

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


API.add_route('/users', UserResource())
API.add_route('/users/{user_id}', UserDetailsResource())
