"""Preserve Arrow null and IEEE NaN distinctions in nullable floating arrays."""
from __future__ import annotations

import numpy as np
import pandas as pd


def nullable_float_array(values: list[object], dtype: str) -> pd.arrays.FloatingArray:
    mask = np.asarray([value is pd.NA or value is None for value in values], dtype=bool)
    numeric = np.asarray([0 if missing else value for value, missing in zip(values, mask)],
                         dtype=np.float32 if dtype == 'Float32' else np.float64)
    return pd.arrays.FloatingArray(numeric, mask)
