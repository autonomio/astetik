"""Import-compatible v1 helpers with explicit scientific migration errors."""
from __future__ import annotations

from typing import NoReturn

from .._legacy import migration


def _thousand_sep(*_args: object, **_kwargs: object) -> NoReturn:
    """Reject the unsupported v1 operation with a machine-readable recovery."""
    migration('astetik.style.formats._thousand_sep', 'Declare design through astetik.Manifest and semantic colours through astetik.ColorSystem.')


__all__ = ['_thousand_sep']
