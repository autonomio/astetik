"""Grid figures: axis labels on the outer panels, plot areas in the declared proportions."""

from __future__ import annotations

from typing import Protocol, TypedDict, Unpack, cast

from matplotlib.axes import Axes
from matplotlib.figure import Figure

from ._plot_backend import drawing
from ._presentation_headings import heading
from ._presentation_layout import solve_layout
from ._presentation_legend import placement_of

SHARED = '_astetik_shared_axes'
BAND = '_astetik_legend_band'


class _Shown(TypedDict):
    labelbottom: bool


class _TickLabels(Protocol):
    def set_tick_params(self, **kwargs: Unpack[_Shown]) -> None: ...


def plot_axes(figure: Figure) -> list[Axes]:
    """The drawn data axes of a figure, in grid order; colour bars and empty cells are not plots."""
    return [
        ax for ax in figure.axes
        if ax.get_visible() and ax.axison and ax.get_subplotspec() is not None
        and not hasattr(ax, '_colorbar')
    ]


def outer_labels(figure: Figure) -> None:
    """Panels sharing their axes state each axis once: at the bottom of a column, left of a row."""
    plots = plot_axes(figure)
    if not getattr(figure, SHARED, False) or len(plots) < 2:
        return
    cells = {ax: ax.get_subplotspec() for ax in plots}
    for ax, cell in cells.items():
        if cell is None:
            continue
        below = any(
            other is not None
            and other.colspan.start == cell.colspan.start
            and other.rowspan.start > cell.rowspan.start
            for other in cells.values()
        )
        cast(_TickLabels, ax.xaxis).set_tick_params(labelbottom=not below)
        if below:
            drawing(ax).set_xlabel('')
        if cell.colspan.start:
            drawing(ax).set_ylabel('')


def proportion(figure: Figure, aspect: float) -> None:
    """Lengthen or shorten a grid figure until each plot area has the declared aspect."""
    plots = plot_axes(figure)
    cell = plots[0].get_subplotspec() if len(plots) > 1 else None
    if cell is None:
        return
    rows = cell.get_gridspec().nrows
    for _ in range(4):
        solve_layout(figure)
        frame = plots[0].get_window_extent()
        short = (frame.width / aspect - frame.height) / figure.dpi
        if abs(short) < 0.005:
            return
        figure.set_figheight(figure.get_figheight() + short * rows)


def settle_bands(figure: Figure) -> None:
    """Lift headings over legends set above their axes and lengthen the figure to match.

    A legend above the axes takes a band of the page; each grid row's tallest band is
    added to the figure height, so the plots keep the proportions the manifest declares.
    """
    setattr(figure, BAND, 0.0)
    above = [placement_of(ax.get_legend()) for ax in figure.axes]
    if not any(placement is not None and placement.loc == 'outside top' for placement in above):
        return
    solve_layout(figure)
    bands: dict[int, float] = {}
    rows: dict[Axes, int] = {}
    for ax in figure.axes:
        legend, cell = ax.get_legend(), ax.get_subplotspec()
        if cell is None or not ax.get_visible():
            continue
        rows[ax] = cell.rowspan.start
        placement = placement_of(legend)
        if legend is not None and placement is not None and placement.loc == 'outside top':
            band = (legend.get_window_extent().y1 - ax.get_window_extent().y1) / figure.dpi
            bands[rows[ax]] = max(bands.get(rows[ax], 0.0), band)
    for ax, row in rows.items():
        # Headings of one row share a baseline, above the tallest legend band of that row.
        if bands.get(row) and ax.get_title(loc='left'):
            heading(ax, ax.get_title(loc='left'), bands[row] * 72 + 5.0)
    extra = sum(bands.values())
    setattr(figure, BAND, extra)
    if extra:
        figure.set_figheight(figure.get_figheight() + extra)
