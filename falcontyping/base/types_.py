"""Types."""
from typing import Any, List, Optional, TypeVar

T = TypeVar('T')


class RequestAnnotation:

    def __init__(self, type_: T, name: Optional[str]) -> None:
        self.name: Optional[str] = name
        self.wrapped_type = type_

        self.is_usable = type_ not in (Any, type(None))


class Path(RequestAnnotation):

    def __init__(self, type_: T, name: Optional[str]) -> None:
        super().__init__(type_, name)

    def __str__(self) -> str:
        return f'Path(name={self.name}, type={self.wrapped_type})'


class Query(RequestAnnotation):

    def __init__(self, type_: T, name: Optional[str]) -> None:
        super().__init__(type_, name)

    def __str__(self) -> str:
        return f'Query(name={self.name}, type={self.wrapped_type})'


class Body(RequestAnnotation):

    def __init__(self, type_: T, name: Optional[str]) -> None:
        super().__init__(type_, name)

    def __str__(self) -> str:
        return f'Body(name={self.name}, type={self.wrapped_type})'


class HTTPMethodAnnotation:

    def __init__(self,
                 path: List[Path],
                 query: Optional[Query] = None,
                 body: Optional[Body] = None,
                 returns: Optional[Any] = None) -> None:
        self.path = path
        self.query = query
        self.body = body

        self.returns = returns

    def __str__(self) -> str:
        path = ', '.join(
            map(str, self.path)
        )
        return f'HTTPMethodAnnotation(path=[{path}], query={self.query}, body={self.body}, returns={self.returns})'
