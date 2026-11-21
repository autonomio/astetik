"""Typed contracts for the Matplotlib calls that draw publication marks."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Protocol, TypeAlias, TypedDict, Unpack, cast

import numpy as np
from matplotlib.axes import Axes
from matplotlib.collections import PathCollection
from matplotlib.lines import Line2D
from matplotlib.patheffects import AbstractPathEffect
from matplotlib.text import Annotation
from numpy.typing import NDArray

from ._types import FloatArray

Values: TypeAlias = NDArray[np.generic]
Rgba: TypeAlias = tuple[float, float, float, float]


class LinePaint(TypedDict, total=False):
    color: str
    linewidth: float
    alpha: float
    marker: str | None
    markersize: float
    markerfacecolor: str
    markeredgecolor: str
    markeredgewidth: float
    linestyle: str
    drawstyle: str
    path_effects: list[AbstractPathEffect]
    zorder: float


class BandPaint(TypedDict, total=False):
    facecolor: str | Rgba
    edgecolor: str
    alpha: float
    linewidth: float
    zorder: float


class ErrorPaint(TypedDict, total=False):
    yerr: FloatArray
    xerr: FloatArray
    fmt: str
    ecolor: str
    elinewidth: float
    capsize: float
    capthick: float
    zorder: float


class PointPaint(TypedDict, total=False):
    s: float
    color: str
    alpha: float
    marker: str | None
    edgecolors: str
    linewidths: float
    zorder: float


class BarPaint(TypedDict, total=False):
    color: str
    alpha: float
    edgecolor: str
    linewidth: float


class BoxPaint(TypedDict, total=False):
    positions: list[float]
    widths: float
    orientation: str
    patch_artist: bool
    manage_ticks: bool
    showmeans: bool
    boxprops: Mapping[str, object]
    medianprops: Mapping[str, object]
    whiskerprops: Mapping[str, object]
    capprops: Mapping[str, object]
    flierprops: Mapping[str, object]
    meanprops: Mapping[str, object]


class NotePaint(TypedDict, total=False):
    xy: tuple[object, float]
    xytext: tuple[float, float]
    textcoords: str
    ha: str
    va: str
    fontsize: float
    annotation_clip: bool


class Marks(Protocol):
    def plot(self, _x: Values, _y: Values, /, **kwargs: Unpack[LinePaint]) -> list[Line2D]: ...
    def fill_between(
        self, _x: Values, _y1: Values, _y2: Values, /, **kwargs: Unpack[BandPaint]
    ) -> object: ...
    def fill_betweenx(
        self, _y: Values, _x1: Values, _x2: Values, /, **kwargs: Unpack[BandPaint]
    ) -> object: ...
    def errorbar(self, _x: Values, _y: Values, /, **kwargs: Unpack[ErrorPaint]) -> object: ...
    def scatter(
        self, _x: Values, _y: Values, /, **kwargs: Unpack[PointPaint]
    ) -> PathCollection: ...
    def bar(
        self, _x: float, _height: float, _width: float, /, **kwargs: Unpack[BarPaint]
    ) -> object: ...
    def barh(
        self, _y: float, _width: float, _height: float, /, **kwargs: Unpack[BarPaint]
    ) -> object: ...
    def bxp(
        self, _stats: Sequence[Mapping[str, object]], /, **kwargs: Unpack[BoxPaint]
    ) -> object: ...
    def annotate(self, _text: str, /, **kwargs: Unpack[NotePaint]) -> Annotation: ...


def marks(ax: Axes) -> Marks:
    return cast(Marks, ax)
