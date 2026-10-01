"""Versioned, immutable scientific design policy."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Unpack

from ._color_math import (
    check_categories as check_categories,
)
from ._color_math import (
    color_distance as color_distance,
)
from ._color_math import (
    contrast_ratio as contrast_ratio,
)
from ._color_math import (
    lab_components as lab_components,
)
from ._color_math import (
    normalize_hex as normalize_hex,
)
from ._color_math import (
    rgb_components as rgb_components,
)
from ._design_rc import dimensions_for, rc_settings
from ._font import resolve_font
from ._immutable import freeze_mapping
from ._manifest_load import load_document
from ._manifest_sections import (
    axes_section,
    bind_sections,
    categories_section,
    colors_section,
    mapping,
    paper_section,
    typography_section,
)
from ._manifest_types import (
    Axes as Axes,
)
from ._manifest_types import (
    FontInfo as FontInfo,
)
from ._manifest_types import (
    ManifestDocument as ManifestDocument,
)
from ._manifest_types import (
    ManifestSections,
)
from ._manifest_types import (
    Paper as Paper,
)
from ._manifest_types import (
    Typography as Typography,
)

_SCHEMA_VERSION = "1.0"
@dataclass(frozen=True, init=False)
class Manifest:
    """One immutable policy shared by every plot and publication export.

    Sections accept partial values. Sizes are points; widths millimetres.
    Unknown fields reject misspelled scientific design choices.
    """

    schema_version: str
    colors: Mapping[str, str]
    categories: Mapping[str, str]
    typography: Typography
    paper: Paper
    axes: Axes
    _font_info: FontInfo = field(repr=False, compare=False)

    def __init__(self, schema_version: str = _SCHEMA_VERSION,
                 *positional: Mapping[str, object], **sections: Unpack[ManifestSections]) -> None:
        if schema_version != _SCHEMA_VERSION:
            raise ValueError(f"Unsupported manifest schema_version {schema_version!r}; expected {_SCHEMA_VERSION!r}")
        supplied = bind_sections(positional, sections)
        colors = colors_section(supplied.get('colors', {}))
        categories = categories_section(supplied.get('categories', {}), colors)
        typography = typography_section(supplied.get('typography', {}))
        paper = paper_section(supplied.get('paper', {}))
        axes = axes_section(supplied.get('axes', {}))
        object.__setattr__(self, 'schema_version', schema_version)
        object.__setattr__(self, 'colors', MappingProxyType(colors))
        object.__setattr__(self, 'categories', MappingProxyType(categories))
        object.__setattr__(self, 'typography', freeze_mapping(typography))
        object.__setattr__(self, 'paper', freeze_mapping(paper))
        object.__setattr__(self, 'axes', freeze_mapping(axes))
        object.__setattr__(self, '_font_info', freeze_mapping(resolve_font(typography)))

    @classmethod
    def from_dict(cls, document: object) -> Manifest:
        policy = mapping(document, 'A manifest document')
        unknown = set(policy) - {'schema_version', 'colors', 'categories', 'typography', 'paper', 'axes'}
        if unknown:
            raise ValueError(f"Unknown manifest fields: {', '.join(sorted(unknown))}")
        schema_version = policy.get('schema_version', _SCHEMA_VERSION)
        if not isinstance(schema_version, str):
            raise ValueError('schema_version must be a string')
        return cls(schema_version,
                   colors=mapping(policy.get('colors', {}), 'colors'),
                   categories=mapping(policy.get('categories', {}), 'categories'),
                   typography=mapping(policy.get('typography', {}), 'typography'),
                   paper=mapping(policy.get('paper', {}), 'paper'),
                   axes=mapping(policy.get('axes', {}), 'axes'))

    @classmethod
    def load(cls, path: str | Path) -> Manifest:
        return cls.from_dict(load_document(Path(path)))

    def to_dict(self) -> ManifestDocument:
        return {'schema_version': self.schema_version, 'colors': dict(self.colors),
                'categories': dict(self.categories), 'typography': self.typography.copy(),
                'paper': self.paper.copy(), 'axes': {
                    'linewidth': self.axes['linewidth'], 'grid': self.axes['grid'],
                    'spines': list(self.axes['spines']), 'tick_direction': self.axes['tick_direction'],
                    'tick_length': self.axes['tick_length']}}

    def with_primary(self, color: str) -> Manifest:
        document = self.to_dict()
        primary = normalize_hex(color, 'colors.primary')
        if document['colors']['positive'] == document['colors']['primary']:
            document['colors']['positive'] = primary
        document['colors']['primary'] = primary
        return self.from_dict(document)

    @property
    def font_path(self) -> str:
        return self._font_info['path']

    @property
    def font_info(self) -> FontInfo:
        return self._font_info

    def dimensions(self, paper: bool = False, panels: int = 1) -> tuple[float, float]:
        return dimensions_for(self.paper, paper, panels)

    def rc(self, paper: bool = False) -> dict[str, object]:
        """Return local rc_context settings without mutating global state."""
        return rc_settings(self, paper)
