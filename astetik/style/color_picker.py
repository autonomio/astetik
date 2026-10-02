"""Import-compatible v1 helpers with explicit scientific migration errors."""
from __future__ import annotations

from typing import NoReturn

from .._legacy import migration


def color_picker(*_args: object, **_kwargs: object) -> NoReturn:
    """Reject the unsupported v1 operation with a machine-readable recovery."""
    migration('astetik.style.color_picker.color_picker', 'Declare design through astetik.Manifest and semantic colours through astetik.ColorSystem.')


def color_blind(*_args: object, **_kwargs: object) -> NoReturn:
    """Reject the unsupported v1 operation with a machine-readable recovery."""
    migration('astetik.style.color_picker.color_blind', 'Declare design through astetik.Manifest and semantic colours through astetik.ColorSystem.')


def cmaps(*_args: object, **_kwargs: object) -> NoReturn:
    """Reject the unsupported v1 operation with a machine-readable recovery."""
    migration('astetik.style.color_picker.cmaps', 'Declare design through astetik.Manifest and semantic colours through astetik.ColorSystem.')


def _label_to_hex(*_args: object, **_kwargs: object) -> NoReturn:
    """Reject the unsupported v1 operation with a machine-readable recovery."""
    migration('astetik.style.color_picker._label_to_hex', 'Declare design through astetik.Manifest and semantic colours through astetik.ColorSystem.')


__all__ = ['_label_to_hex', 'cmaps', 'color_blind', 'color_picker']
