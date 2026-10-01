"""Normalize supported scientific scalars without modifying their values."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import cast

import numpy as np
import pandas as pd

from ._types import JsonObject, JsonValue


def scalar(value: object) -> JsonValue:
    if isinstance(value, np.generic):
        value = cast(object, value.item())
    if isinstance(value, (pd.Timestamp, pd.Timedelta)):
        return value.isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (list, tuple)):
        return [scalar(v) for v in cast(Iterable[object], value)]
    if isinstance(value, Mapping):
        result: JsonObject = {}
        for key, item in cast(Mapping[object, object], value).items():
            if not isinstance(key, str):
                raise ValueError('Plotted mappings require string keys.')
            result[key] = scalar(item)
        return result
    raise ValueError(f'Unsupported plotted scalar {value!r}.')
