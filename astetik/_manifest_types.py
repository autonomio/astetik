"""Validated design policy domains and their serialized representation."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Literal, TypedDict

Spine = Literal['left', 'right', 'top', 'bottom']
TickDirection = Literal['in', 'out', 'inout']
PaperPreset = Literal['single', 'double']


class Typography(TypedDict):
    """Resolved type sizes in points and explicit font selection."""

    font: str
    font_path: str | None
    fontsize: float
    labelsize: float
    titlesize: float
    ticksize: float
    legendsize: float


class Paper(TypedDict):
    """Final physical dimensions and raster resolution."""

    preset: PaperPreset
    width_mm: float
    aspect: float
    dpi: int
    min_fontsize: float


class Axes(TypedDict):
    """Visible axis geometry and grid settings."""

    linewidth: float
    grid: bool
    spines: tuple[Spine, ...]
    tick_direction: TickDirection
    tick_length: float


class FontInfo(TypedDict):
    """Exact resolved font file and its content identity."""

    requested: str
    resolved: str
    path: str
    sha256: str
    fallback: bool


class ManifestSections(TypedDict, total=False):
    """Partial user mappings validated by Manifest at its input boundary."""

    colors: Mapping[str, object]
    categories: Mapping[str, object]
    typography: Mapping[str, object]
    paper: Mapping[str, object]
    axes: Mapping[str, object]


class SerializedAxes(TypedDict):
    """JSON uses an ordered list for axis spines."""

    linewidth: float
    grid: bool
    spines: list[Spine]
    tick_direction: TickDirection
    tick_length: float


class ManifestDocument(TypedDict):
    """The complete portable design document."""

    schema_version: str
    colors: dict[str, str]
    categories: dict[str, str]
    typography: Typography
    paper: Paper
    axes: SerializedAxes
