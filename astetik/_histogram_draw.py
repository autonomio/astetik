"""Histogram marks, overlays, legend, and value axis on one axes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol, TypedDict, Unpack, cast

import numpy as np
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.colors import to_rgba
from matplotlib.container import BarContainer
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.patheffects import AbstractPathEffect, withStroke
from matplotlib.transforms import Transform

from ._histogram_bins import bar_spans
from ._plot_backend import SharingAxes, disable_grid
from ._presentation_legend import Placement, place_legend
from ._presentation_ticks import value_locator
from ._types import FloatArray

Reference = Literal['mean', 'median']
_DASHES: dict[Reference, Literal['dashed', 'dotted']] = {'mean': 'dashed', 'median': 'dotted'}


class _BarPaint(TypedDict):
    align: str
    facecolor: str
    edgecolor: str
    linewidth: float
    alpha: float


class _StairPaint(TypedDict):
    baseline: FloatArray | None
    orientation: str
    fill: bool
    color: str
    linewidth: float
    alpha: float


class _RulePaint(TypedDict, total=False):
    transform: Transform
    colors: str
    linewidth: float
    linestyles: str
    alpha: float


class _CurvePaint(TypedDict):
    color: str
    linewidth: float
    path_effects: list[AbstractPathEffect]


class _Marks(Protocol):
    def bar(
        self, x: FloatArray, height: FloatArray, width: FloatArray, bottom: FloatArray,
        **kwargs: Unpack[_BarPaint],
    ) -> BarContainer: ...
    def barh(
        self, y: FloatArray, width: FloatArray, height: FloatArray, left: FloatArray,
        **kwargs: Unpack[_BarPaint],
    ) -> BarContainer: ...
    def stairs(
        self, values: FloatArray, edges: FloatArray, **kwargs: Unpack[_StairPaint]
    ) -> object: ...
    def vlines(
        self, _x: FloatArray | float, _ymin: float, _ymax: float, /, **kwargs: Unpack[_RulePaint]
    ) -> object: ...
    def hlines(
        self, _y: FloatArray | float, _xmin: float, _xmax: float, /, **kwargs: Unpack[_RulePaint]
    ) -> object: ...
    def plot(self, x: FloatArray, y: FloatArray, **kwargs: Unpack[_CurvePaint]) -> object: ...


@dataclass(frozen=True)
class Style:
    """Resolved presentation shared by every series on one histogram axes."""

    horizontal: bool
    log: bool
    step: bool
    fill: bool
    alpha: float
    shrink: float
    edgecolor: str | None
    edgewidth: float
    linewidth: float
    paper: str
    legendsize: float
    integer: bool
    cumulative: bool


@dataclass(frozen=True)
class Canvas:
    """One axes, its shared bin boundaries, and its resolved style."""

    ax: Axes
    style: Style
    edges: FloatArray

    def fill(
        self, heights: FloatArray, bottom: FloatArray, color: str, slot: tuple[int, int]
    ) -> None:
        """Paint one series; layered bars sort tallest-behind so none is hidden."""
        marks, style = cast(_Marks, self.ax), self.style
        if style.step:
            if style.fill:
                marks.stairs(
                    bottom + heights, self.edges, baseline=bottom, fill=True, color=color,
                    orientation=self.orientation, linewidth=0, alpha=style.alpha,
                )
            return
        start, width = bar_spans(self.edges, style.shrink, *slot, style.log)
        paint = _BarPaint(
            align='edge', facecolor=color if style.fill else 'none',
            edgecolor=style.edgecolor or color, linewidth=style.edgewidth, alpha=style.alpha,
        )
        bars = (
            marks.barh(start, heights, width, bottom, **paint)
            if style.horizontal
            else marks.bar(start, heights, width, bottom, **paint)
        )
        tallest = float(heights.max()) or 1.0
        for patch, height in zip(bars.patches, heights):
            patch.set_zorder(1.5 - 0.5 * float(height) / tallest)

    def outline(self, heights: FloatArray, bottom: FloatArray, color: str) -> None:
        """Trace a step series above every fill so each silhouette stays readable."""
        style = self.style
        if style.step and style.edgewidth:
            # A cumulative outline stays open: closing it would draw a false drop.
            cast(_Marks, self.ax).stairs(
                bottom + heights, self.edges, fill=False, color=style.edgecolor or color,
                baseline=None if style.cumulative else bottom,
                orientation=self.orientation, linewidth=style.edgewidth, alpha=1.0,
            )

    @property
    def orientation(self) -> str:
        return 'horizontal' if self.style.horizontal else 'vertical'

    def rug(self, values: FloatArray, color: str) -> None:
        """Mark every observation along the bin axis; height is 3% of the axes."""
        marks, ax = cast(_Marks, self.ax), self.ax
        if self.style.horizontal:
            marks.hlines(
                values, 0.0, 0.03, transform=ax.get_yaxis_transform(), colors=color,
                linewidth=0.5, alpha=0.5,
            )
        else:
            marks.vlines(
                values, 0.0, 0.03, transform=ax.get_xaxis_transform(), colors=color,
                linewidth=0.5, alpha=0.5,
            )

    def curve(self, support: FloatArray, density: FloatArray, color: str) -> None:
        """Draw a density estimate with a paper halo so it reads across filled bins."""
        width = self.style.linewidth
        x, y = (density, support) if self.style.horizontal else (support, density)
        cast(_Marks, self.ax).plot(
            x, y, color=color, linewidth=width,
            path_effects=[withStroke(linewidth=width + 1.5, foreground=self.style.paper)],
        )

    def reference(self, name: Reference, value: float, top: float, color: str) -> None:
        """Rule a statistic from the baseline to the tallest bin, never into the legend."""
        marks = cast(_Marks, self.ax)
        rule = marks.hlines if self.style.horizontal else marks.vlines
        rule(value, 0.0, top, colors=color, linewidth=self.style.linewidth,
             linestyles=_DASHES[name])

    def series_handle(self, color: str, label: str) -> Artist:
        """A legend key painted exactly as the series' bins are painted."""
        style = self.style
        edge, face = style.edgecolor or color, color if style.fill else 'none'
        if style.step:
            return Patch(
                facecolor=to_rgba(face, style.alpha if style.fill else 0.0), label=label,
                edgecolor=edge if style.edgewidth else 'none', linewidth=style.edgewidth,
            )
        return Patch(
            facecolor=face, edgecolor=edge, linewidth=style.edgewidth, alpha=style.alpha,
            label=label,
        )

    def reference_handle(self, name: Reference, color: str) -> Artist:
        return Line2D(
            [], [], color=color, linewidth=self.style.linewidth, linestyle=_DASHES[name],
            label=name.capitalize(),
        )

    def legend(self, loc: str, handles: list[Artist], notes: list[str]) -> None:
        """Declare series, reference, and sample-size entries at the requested position."""
        entries = [*handles, *(Patch(facecolor='none', edgecolor='none', label=n) for n in notes)]
        if entries:
            place_legend(self.ax, Placement(loc, entries, self.style.legendsize, not handles))

    def value_axis(self) -> None:
        """End the zero-based value axis on a labelled tick at or above every bin."""
        ax, horizontal = self.ax, self.style.horizontal
        sharing = cast(SharingAxes, ax)
        shared = sharing.get_shared_x_axes() if horizontal else sharing.get_shared_y_axes()
        top = 0.0
        for sibling in shared.get_siblings(ax):
            interval = sibling.dataLim.intervalx if horizontal else sibling.dataLim.intervaly
            if np.isfinite(interval).all():
                top = max(top, float(interval[1]))
        limit = float(value_locator(self.style.integer).tick_values(0.0, top or 1.0)[-1])
        (ax.set_xlim if horizontal else ax.set_ylim)(0.0, limit)
        disable_grid(ax.yaxis if horizontal else ax.xaxis)
