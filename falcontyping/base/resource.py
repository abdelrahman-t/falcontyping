"""Resource."""
from typing import Dict, Optional


class TypedResource:

    methods_body_parameter: Dict[str, Optional[str]]
    hints: Dict[str, Dict]
