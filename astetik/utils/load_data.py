"""Import-compatible v1 helpers with explicit scientific migration errors."""
from __future__ import annotations

from typing import NoReturn

from .._legacy import migration


def read(*_args: object, **_kwargs: object) -> NoReturn:
    """Reject the unsupported v1 operation with a machine-readable recovery."""
    migration('astetik.utils.load_data.read', 'Use an explicit preparation step with retained input and receipt before astetik.render.')
