"""Resolve and fingerprint the exact runtime font selected by a manifest."""
from __future__ import annotations

import threading
from collections.abc import Callable
from hashlib import sha256
from typing import cast

from ._font_source import FontSource, select_font
from ._manifest_types import FontInfo, Typography

_FONT_REGISTRATION_LOCK = threading.Lock()
_REGISTERED_FONTS: set[str] = set()


def resolve_font(typography: Typography, context: FontSource | None = None) -> FontInfo:
    from matplotlib import font_manager

    source, fallback, retained = select_font(typography, context)
    if not source.is_file():
        raise ValueError(f'Typography font file does not exist: {source}')
    try:
        resolved = font_manager.FontProperties(fname=str(source)).get_name()
    except (OSError, RuntimeError) as exc:
        raise ValueError(f'Cannot read typography font: {source}') from exc
    identity: FontInfo = {'requested': typography['font'], 'resolved': resolved,
                         'path': str(source.resolve()), 'sha256': sha256(source.read_bytes()).hexdigest(),
                         'fallback': fallback}
    if retained and any(identity[name] != retained[name] for name in ('requested', 'resolved', 'sha256')):
        raise ValueError('Retained font identity differs from the selected file or typography declaration')
    # Registration does not change rcParams; rc_context remains fully isolated.
    with _FONT_REGISTRATION_LOCK:
        if identity['path'] not in _REGISTERED_FONTS:
            cast(Callable[[str], None], getattr(font_manager.fontManager, 'addfont'))(identity['path'])
            _REGISTERED_FONTS.add(identity['path'])
    return identity
