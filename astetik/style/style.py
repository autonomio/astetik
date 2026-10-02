"""Import-compatible v1 helpers with explicit scientific migration errors."""
from __future__ import annotations

from typing import NoReturn

from .._legacy import migration


def default_colors(*_args: object, **_kwargs: object) -> NoReturn:
    """Reject the unsupported v1 operation with a machine-readable recovery."""
    migration('astetik.style.style.default_colors', 'Declare design through astetik.Manifest and semantic colours through astetik.ColorSystem.')


def params(*_args: object, **_kwargs: object) -> NoReturn:
    """Reject the unsupported v1 operation with a machine-readable recovery."""
    migration('astetik.style.style.params', 'Declare design through astetik.Manifest and semantic colours through astetik.ColorSystem.')


def styles(*_args: object, **_kwargs: object) -> NoReturn:
    """Reject the unsupported v1 operation with a machine-readable recovery."""
    migration('astetik.style.style.styles', 'Declare design through astetik.Manifest and semantic colours through astetik.ColorSystem.')
