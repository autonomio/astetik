"""Select runtime font files without changing serialized design declarations."""
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Protocol, TypedDict, Unpack, cast

from ._manifest_types import FontInfo, Typography

FontSource = str | Path | FontInfo
_FONT_FIELDS = {'requested', 'resolved', 'path', 'sha256', 'fallback'}


class _FontOptions(TypedDict):
    """Explicit external resolver keyword policy."""

    fallback_to_default: bool


class _FontResolver(Protocol):
    def __call__(self, family: str, **_kwargs: Unpack[_FontOptions]) -> str: ...


def font_identity(value: object) -> FontInfo:
    """Validate the complete retained identity before using its file context."""
    if not isinstance(value, Mapping):
        raise ValueError('Font identity must be an object')
    record = cast(Mapping[str, object], value)
    if set(record) != _FONT_FIELDS:
        raise ValueError('Font identity must contain requested, resolved, path, sha256 and fallback')
    if any(not isinstance(record[field], str) or not record[field] for field in _FONT_FIELDS - {'fallback'}):
        raise ValueError('Font identity text fields must be nonempty strings')
    if not isinstance(record['fallback'], bool):
        raise ValueError('Font fallback must be a boolean')
    checksum = cast(str, record['sha256'])
    if len(checksum) != 64 or any(character not in '0123456789abcdef' for character in checksum):
        raise ValueError('Font sha256 must be a lowercase SHA256 digest')
    return cast(FontInfo, dict(record))


def select_font(typography: Typography, context: FontSource | None) -> tuple[Path, bool, FontInfo | None]:
    from matplotlib import font_manager, get_data_path

    retained = None
    if context is not None and not isinstance(context, (str, Path)):
        retained = font_identity(context)
        if retained['requested'] != typography['font']:
            raise ValueError('Retained font request differs from the typography declaration')
        if retained['fallback'] and (typography['font_path'] or typography['font'] == 'Finlandica'):
            raise ValueError('Explicit or bundled Finlandica selection cannot be a fallback')
        return Path(retained['path']).expanduser().resolve(), retained['fallback'], retained
    explicit = context if context is not None else typography['font_path']
    if explicit:
        return Path(explicit).expanduser().resolve(), False, retained
    if typography['font'] == 'Finlandica':
        return Path(__file__).with_name('fonts') / 'Finlandica.ttf', False, retained
    try:
        selected = cast(_FontResolver, getattr(font_manager, 'findfont'))(typography['font'], fallback_to_default=False)
    except ValueError:
        return Path(get_data_path()) / 'fonts' / 'ttf' / 'DejaVuSans.ttf', True, retained
    return Path(selected), False, retained
