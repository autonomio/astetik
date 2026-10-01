"""Resolve and fingerprint the explicit font used by a design manifest."""
from __future__ import annotations

import threading
from collections.abc import Callable
from hashlib import sha256
from pathlib import Path
from typing import Protocol, TypedDict, Unpack, cast

from ._manifest_types import FontInfo, Typography

_FONT_REGISTRATION_LOCK = threading.Lock()
_REGISTERED_FONTS: set[str] = set()


class _FontOptions(TypedDict):
    """Explicit external resolver keyword policy."""

    fallback_to_default: bool


class _FontResolver(Protocol):
    def __call__(self, family: str, **kwargs: Unpack[_FontOptions]) -> str: ...


def resolve_font(typography: Typography) -> FontInfo:
    from matplotlib import font_manager, get_data_path
    requested = typography["font"]
    explicit = typography["font_path"]
    fallback = False
    if explicit:
        source = Path(explicit).expanduser().resolve()
        if not source.is_file():
            raise ValueError(f"Typography font_path does not exist: {source}")
    elif requested == "Finlandica":
        source = Path(__file__).with_name("fonts") / "Finlandica.ttf"
        if not source.is_file():
            raise ValueError("Bundled Finlandica is missing; repair the package installation")
    else:
        try:
            source = Path(cast(_FontResolver, getattr(font_manager, "findfont"))(requested, fallback_to_default=False))
        except ValueError:
            source = Path(get_data_path()) / "fonts" / "ttf" / "DejaVuSans.ttf"
            fallback = True
    try:
        resolved = font_manager.FontProperties(fname=str(source)).get_name()
    except (OSError, RuntimeError) as exc:
        raise ValueError(f"Cannot read typography font: {source}") from exc
    # Font registration does not change rcParams; rc_context remains fully isolated.
    resolved_path = str(source.resolve())
    with _FONT_REGISTRATION_LOCK:
        if resolved_path not in _REGISTERED_FONTS:
            cast(Callable[[str], None], getattr(font_manager.fontManager, "addfont"))(resolved_path)
            _REGISTERED_FONTS.add(resolved_path)
    return {"requested": requested, "resolved": resolved, "path": str(source.resolve()),
            "sha256": sha256(source.read_bytes()).hexdigest(), "fallback": fallback}


