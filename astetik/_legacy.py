"""Unsupported v1 helpers fail with explicit v2 scientific migration guidance."""
from __future__ import annotations

from typing import NoReturn

from ._errors import AstetikError


def migration(feature: str, recovery: str) -> NoReturn:
    raise AstetikError('LEGACY_API', f'{feature} is unsupported in Astetik 2.0.', {'recovery': recovery})
