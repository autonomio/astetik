"""Import-compatible v1 helpers with explicit scientific migration errors."""
from __future__ import annotations

from typing import NoReturn

from .._legacy import migration


def _header(*_args: object, **_kwargs: object) -> NoReturn:
    """Reject the unsupported v1 operation with a machine-readable recovery."""
    migration('astetik.style.template._header', 'Declare design through astetik.Manifest and semantic colours through astetik.ColorSystem.')


def _footer(*_args: object, **_kwargs: object) -> NoReturn:
    """Reject the unsupported v1 operation with a machine-readable recovery."""
    migration('astetik.style.template._footer', 'Declare design through astetik.Manifest and semantic colours through astetik.ColorSystem.')


__all__ = ['_footer', '_header']
