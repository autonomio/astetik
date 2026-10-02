"""Exact keyword contracts for Astetik's native Matplotlib drawing operations."""

from __future__ import annotations

from typing import Literal, TypedDict

from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.colors import Colormap, Normalize

from ._types import FloatArray


class ScatterStyle(TypedDict, total=False):
    c: FloatArray
    color: str
    cmap: Colormap
    norm: Normalize
    s: float
    alpha: float
    marker: str | None
    edgecolors: str
    linewidths: float
    label: str | None


class LineStyle(TypedDict, total=False):
    color: str
    linewidth: float
    alpha: float
    marker: str | None
    linestyle: str
    drawstyle: str
    label: str | None


class BarStyle(TypedDict, total=False):
    width: float | FloatArray
    yerr: float | None
    xerr: float | None
    color: str
    alpha: float
    edgecolor: str
    linewidth: float
    align: Literal['center', 'edge']


class HorizontalBarStyle(TypedDict, total=False):
    height: float | FloatArray
    xerr: float | None
    color: str
    alpha: float
    edgecolor: str
    linewidth: float
    align: Literal['center', 'edge']


class FillStyle(TypedDict, total=False):
    color: str
    facecolor: str
    edgecolor: str
    alpha: float


class ContourStyle(TypedDict):
    levels: FloatArray
    cmap: Colormap
    norm: Normalize


class ImageStyle(TypedDict):
    cmap: Colormap
    vmin: float
    vmax: float
    aspect: str
    interpolation: str


class BoxStyle(TypedDict):
    positions: list[float]
    widths: float
    orientation: Literal['horizontal', 'vertical']
    patch_artist: bool
    manage_ticks: bool
    boxprops: dict[str, str | float]
    medianprops: dict[str, str]
    flierprops: dict[str, str | float]


class PieStyle(TypedDict):
    labels: list[str]
    colors: list[str]
    startangle: float
    autopct: str | None
    textprops: dict[str, float]
    wedgeprops: dict[str, str | float]


class ErrorbarStyle(TypedDict):
    yerr: FloatArray
    color: str
    marker: str
    markersize: float
    linewidth: float
    capsize: float


class TextStyle(TypedDict, total=False):
    ha: str
    va: str
    color: str
    transform: object


class ColorbarStyle(TypedDict, total=False):
    ax: Axes
    label: str
    ticks: list[float]
    orientation: Literal['vertical', 'horizontal']
    fraction: float
    pad: float


class LegendStyle(TypedDict, total=False):
    handles: list[Artist]
    frameon: bool
    loc: str


class TickStyle(TypedDict):
    colors: str
    direction: Literal['in', 'out', 'inout']
    length: float
    width: float


class GridStyle(TypedDict):
    color: str
    linewidth: float
    alpha: float


class TitleStyle(TypedDict):
    x: float
    ha: str
    va: str
    fontsize: float
    fontweight: str


class EventStyle(TypedDict):
    colors: str
    linewidths: float


class TickLabelsStyle(TypedDict, total=False):
    rotation: float
    ha: str
