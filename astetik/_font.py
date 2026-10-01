"""Resolve and fingerprint the exact runtime font selected by a manifest."""
from __future__ import annotations

import os
import threading
from collections.abc import Callable
from hashlib import sha256
from typing import Protocol, cast

from ._font_source import FontSource, select_font
from ._manifest_types import FontInfo, Typography

_FONT_REGISTRATION_LOCK = threading.Lock()
_REGISTERED_FONTS: dict[str, str] = {}


class _CachedFont(Protocol):
    def cache_clear(self) -> None: ...


class _FontEntry(Protocol):
    @property
    def fname(self) -> str: ...


def resolve_font(typography: Typography, context: FontSource | None = None) -> FontInfo:
    from matplotlib import font_manager

    source, fallback, retained = select_font(typography, context)
    if not source.is_file():
        raise ValueError(f'Typography font file does not exist: {source}')
    path, checksum = str(source.resolve()), sha256(source.read_bytes()).hexdigest()
    # A changed file invalidates Matplotlib's pathname cache and its old entries.
    with _FONT_REGISTRATION_LOCK:
        previous = _REGISTERED_FONTS.get(path)
        if previous != checksum:
            _REGISTERED_FONTS.pop(path, None)
            cast(_CachedFont, getattr(font_manager, '_get_font')).cache_clear()
            entries = cast(list[_FontEntry], getattr(font_manager.fontManager, 'ttflist'))
            # Compare canonical strings without constructing a Path for every installed font.
            entries[:] = [entry for entry in entries if os.path.realpath(entry.fname) != path]
        try:
            resolved = font_manager.FontProperties(fname=path).get_name()
        except (OSError, RuntimeError) as exc:
            raise ValueError(f'Cannot read typography font: {source}') from exc
        identity: FontInfo = {'requested': typography['font'], 'resolved': resolved,
                             'path': path, 'sha256': checksum, 'fallback': fallback}
        if retained and any(identity[name] != retained[name] for name in ('requested', 'resolved', 'sha256')):
            raise ValueError('Retained font identity differs from the selected file or typography declaration')
        if previous != checksum:
            cast(Callable[[str], None], getattr(font_manager.fontManager, 'addfont'))(path)
            _REGISTERED_FONTS[path] = checksum
        return identity
