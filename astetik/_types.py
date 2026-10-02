"""Shared finite JSON and scientific array types, compatible with Python 3.11."""
from __future__ import annotations

from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | list['JsonValue'] | dict[str, 'JsonValue']
JsonObject: TypeAlias = dict[str, JsonValue]
FloatArray: TypeAlias = NDArray[np.float64]
