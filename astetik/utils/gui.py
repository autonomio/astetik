"""Import-compatible v1 helpers with explicit scientific migration errors."""
from __future__ import annotations

from typing import NoReturn

from .._legacy import migration


def toggle(*_args: object, **_kwargs: object) -> NoReturn:
    """Reject the unsupported v1 operation with a machine-readable recovery."""
    migration('astetik.utils.gui.toggle', 'Keep notebook presentation and warning policy in the caller; Astetik never changes them globally.')


def warning(*_args: object, **_kwargs: object) -> NoReturn:
    """Reject the unsupported v1 operation with a machine-readable recovery."""
    migration('astetik.utils.gui.warning', 'Keep notebook presentation and warning policy in the caller; Astetik never changes them globally.')
