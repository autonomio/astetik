"""NumPy scalar type views whose runtime classes do not support subscription."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    NumpyScalar = np.generic[object]
    NumpyDateTime = np.datetime64[datetime | date | int | None]
    NumpyDuration = np.timedelta64[timedelta | int | None]
else:
    NumpyScalar = np.generic
    NumpyDateTime = np.datetime64
    NumpyDuration = np.timedelta64
