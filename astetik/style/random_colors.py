"""Import-compatible v1 helpers with explicit scientific migration errors."""
from __future__ import annotations

from typing import NoReturn

from .._legacy import migration


def randomcolor(*_args: object, **_kwargs: object) -> NoReturn:
    """Reject the unsupported v1 operation with a machine-readable recovery."""
    migration('astetik.style.random_colors.randomcolor', 'Declare design through astetik.Manifest and semantic colours through astetik.ColorSystem.')
