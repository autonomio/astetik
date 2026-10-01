"""Explicit font identity, glyph coverage and visible text measurements."""
from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Protocol, TypedDict, Unpack, cast

import numpy as np
from matplotlib import font_manager, ft2font
from matplotlib.backend_bases import RendererBase
from matplotlib.figure import Figure
from matplotlib.text import Text

from ._data import file_digest
from ._json import json_object
from ._result_geometry import clipped
from ._types import JsonObject


@dataclass(frozen=True)
class FontPolicy:
    """Exact publication type selection and minimum size."""

    minimum: float
    path: str | None
    family: str | None
    checksum: str | None


@dataclass
class TextEvidence:
    """Measured text, font and coverage failures."""

    size: list[JsonObject] = field(default_factory=lambda: list[JsonObject]())
    clipped: list[JsonObject] = field(default_factory=lambda: list[JsonObject]())
    fonts: list[JsonObject] = field(default_factory=lambda: list[JsonObject]())
    glyphs: list[JsonObject] = field(default_factory=lambda: list[JsonObject]())


class _FontFindOptions(TypedDict):
    fallback_to_default: bool


class _FontFinder(Protocol):
    def __call__(self, _properties: font_manager.FontProperties, /, **_options: Unpack[_FontFindOptions]) -> str: ...


@lru_cache(maxsize=128)
def font_charmap(path: str, _content_sha256: str) -> frozenset[int]:
    return frozenset(ft2font.FT2Font(path).get_charmap())


def _font_evidence(text: Text, policy: FontPolicy, coverage: dict[Path, frozenset[int]]) -> tuple[JsonObject, JsonObject | None]:
    label = text.get_text()
    try:
        resolved = Path(cast(_FontFinder, getattr(font_manager, 'findfont'))(text.get_fontproperties(), fallback_to_default=False)).resolve()
        family = font_manager.FontProperties(fname=str(resolved)).get_name()
        valid = (not policy.path or resolved == Path(policy.path).expanduser().resolve()) and (
            not policy.family or family == policy.family)
        font: JsonObject = {'text': label, 'path': str(resolved), 'family': family, 'passed': bool(valid)}
        if resolved not in coverage:
            coverage[resolved] = font_charmap(str(resolved), file_digest(resolved))
        missing = sorted({character for character in label if not character.isspace()
                          and ord(character) not in coverage[resolved]}, key=ord)
        glyph = json_object({'text': label, 'font_path': str(resolved),
                             'missing': [{'character': character, 'codepoint': f'U+{ord(character):04X}',
                                          'name': unicodedata.name(character, 'UNNAMED')} for character in missing]}) if missing else None
        return font, glyph
    except (OSError, ValueError, RuntimeError) as error:
        return ({'text': label, 'passed': False, 'reason': str(error)},
                {'text': label, 'reason': 'The actual font could not be read.', 'details': str(error)})


def text_evidence(figure: Figure, renderer: RendererBase, policy: FontPolicy, omitted: set[int]) -> TextEvidence:
    evidence = TextEvidence()
    coverage: dict[Path, frozenset[int]] = {}
    for text in figure.findobj(match=Text):
        if id(text) in omitted or not text.get_visible() or not text.get_text().strip():
            continue
        label = text.get_text()
        points = float(text.get_fontsize())
        if points + 1e-9 < policy.minimum:
            evidence.size.append({'text': label, 'points': points})
        extent = text.get_window_extent(renderer)
        if not np.isfinite(extent.extents).all() or clipped(extent, figure.bbox):
            evidence.clipped.append(json_object({'text': label, 'bounds': list(map(float, extent.extents))}))
        font, glyph = _font_evidence(text, policy, coverage)
        evidence.fonts.append(font)
        if glyph:
            evidence.glyphs.append(glyph)
    return evidence


def checksum_passed(policy: FontPolicy) -> bool:
    return bool(not policy.checksum or (policy.path and Path(policy.path).is_file() and file_digest(policy.path) == policy.checksum))
