"""Precise contracts for the native Matplotlib operations used by Astetik."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from contextlib import AbstractContextManager
from typing import Protocol, TypeAlias, Unpack, cast

import matplotlib
import numpy as np
import pandas as pd
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.collections import EventCollection, FillBetweenPolyCollection, PathCollection
from matplotlib.colorbar import Colorbar
from matplotlib.container import BarContainer, ErrorbarContainer
from matplotlib.contour import QuadContourSet
from matplotlib.figure import Figure
from matplotlib.image import AxesImage
from matplotlib.lines import Line2D
from matplotlib.patches import Wedge
from matplotlib.text import Text
from numpy.typing import NDArray

from ._plot_styles import (
    BarStyle,
    BoxStyle,
    ColorbarStyle,
    ContourStyle,
    ErrorbarStyle,
    EventStyle,
    FillStyle,
    HorizontalBarStyle,
    ImageStyle,
    LegendStyle,
    LineStyle,
    PieStyle,
    ScatterStyle,
    TextStyle,
    TickLabelsStyle,
)
from ._types import FloatArray, JsonScalar

PlotValues: TypeAlias = 'NDArray[np.generic] | Sequence[JsonScalar] | pd.Series[str | int | float | bool | pd.Timestamp]'
Color = str | tuple[float, float, float] | tuple[float, float, float, float]


class DrawingAxes(Protocol):
    def scatter(
        self, x: PlotValues, y: PlotValues, **kwargs: Unpack[ScatterStyle]
    ) -> PathCollection: ...
    def plot(self, x: PlotValues, y: PlotValues, **kwargs: Unpack[LineStyle]) -> list[Line2D]: ...
    def bar(
        self, x: float | PlotValues, height: float | FloatArray, **kwargs: Unpack[BarStyle]
    ) -> BarContainer: ...
    def barh(
        self, y: float | PlotValues, width: float | FloatArray, **kwargs: Unpack[HorizontalBarStyle]
    ) -> BarContainer: ...
    def fill_between(
        self,
        _x: FloatArray,
        _y1: FloatArray,
        _y2: FloatArray | float = 0,
        /,
        **kwargs: Unpack[FillStyle],
    ) -> FillBetweenPolyCollection: ...
    def fill_betweenx(
        self, _y: FloatArray, _x1: FloatArray, _x2: FloatArray, /, **kwargs: Unpack[FillStyle]
    ) -> FillBetweenPolyCollection: ...
    def contour(
        self, x: FloatArray, y: FloatArray, z: FloatArray, **kwargs: Unpack[ContourStyle]
    ) -> QuadContourSet: ...
    def contourf(
        self, x: FloatArray, y: FloatArray, z: FloatArray, **kwargs: Unpack[ContourStyle]
    ) -> QuadContourSet: ...
    def imshow(self, x: FloatArray, **kwargs: Unpack[ImageStyle]) -> AxesImage: ...
    def bxp(
        self, _bxpstats: Sequence[Mapping[str, float | FloatArray]], /, **kwargs: Unpack[BoxStyle]
    ) -> dict[str, list[Artist]]: ...
    def pie(
        self, x: FloatArray, **kwargs: Unpack[PieStyle]
    ) -> tuple[list[Wedge], list[Text], list[Text]]: ...
    def errorbar(
        self, x: float, y: float, **kwargs: Unpack[ErrorbarStyle]
    ) -> ErrorbarContainer: ...
    def eventplot(
        self, _positions: FloatArray, /, **kwargs: Unpack[EventStyle]
    ) -> list[EventCollection]: ...
    def set_xlabel(self, _xlabel: str, /) -> Text: ...
    def set_ylabel(self, _ylabel: str, /) -> Text: ...
    def set_xticks(
        self,
        _ticks: PlotValues,
        _labels: list[str] | None = None,
        /,
        **kwargs: Unpack[TickLabelsStyle],
    ) -> list[Artist]: ...
    def set_yticks(self, ticks: PlotValues, labels: list[str] | None = None) -> list[Artist]: ...
    def legend(self, **kwargs: Unpack[LegendStyle]) -> Artist: ...
    def text(self, x: float, y: float, s: str, **kwargs: Unpack[TextStyle]) -> Text: ...


class ColorbarFigure(Protocol):
    def colorbar(self, _mappable: Artist, /, **kwargs: Unpack[ColorbarStyle]) -> Colorbar: ...


def drawing(ax: Axes) -> DrawingAxes:
    return cast(DrawingAxes, ax)


def colorbar_figure(figure: Figure) -> ColorbarFigure:
    return cast(ColorbarFigure, figure)


class SharedAxes(Protocol):
    def get_siblings(self, axis: Axes) -> list[Axes]: ...


class SharingAxes(Protocol):
    def get_shared_x_axes(self) -> SharedAxes: ...
    def get_shared_y_axes(self) -> SharedAxes: ...


class NativeCanvas(Protocol):
    def draw(self) -> None: ...


class FileFontProperties(Protocol):
    def set_file(self, path: str) -> None: ...


def draw_canvas(figure: Figure) -> None:
    cast(NativeCanvas, figure.canvas).draw()


class NativeGrid(Protocol):
    def grid(self, _visible: bool, /) -> None: ...


def disable_grid(value: object) -> None:
    cast(NativeGrid, value).grid(False)


class ScaleAxes(Protocol):
    def set_xscale(self, scale: str) -> None: ...
    def set_yscale(self, scale: str) -> None: ...


class MatplotlibSettings(Protocol):
    def rc_context(self, rc: dict[str, object]) -> AbstractContextManager[None]: ...


def scoped_rc(settings: Mapping[str, object]) -> AbstractContextManager[None]:
    return cast(MatplotlibSettings, matplotlib).rc_context(dict(settings))
