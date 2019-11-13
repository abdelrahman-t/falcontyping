"""Resource."""
from typing import Any, Dict, List, Optional

from .types_ import HTTPMethodAnnotation

ResponseParameters = List[Any]


class TypedResource:

    def _init_annotations(self) -> None:
        self._annotations: Dict[str, HTTPMethodAnnotation] = {}

    def _set_method_annotations(self, method: str, annotations: HTTPMethodAnnotation) -> None:
        self._annotations[method] = annotations

    @property
    def annotations(self) -> Optional[Dict[str, HTTPMethodAnnotation]]:
        try:
            return self._annotations

        except AttributeError:
            return None

    @annotations.setter
    def annotations(self, value: Any) -> None:
        raise ValueError('Annotations should not be set manually')
